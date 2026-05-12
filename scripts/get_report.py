import requests
import pdfplumber
import json
import os
import re
from datetime import datetime

DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def run():
    # 1. Intentamos encontrar la URL real desde la página de descargas
    base_url = "https://rendivalores.com/informes-diarios/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        print(f"Buscando enlace actualizado en: {base_url}")
        page_response = requests.get(base_url, headers=headers, timeout=20)
        
        # Buscamos patrones de URLs de PDF dentro del código de la página
        pdf_urls = re.findall(r'https://rendivalores\.com/wp-content/uploads/[^"\'>]+\.pdf', page_response.text)
        
        if not pdf_urls:
            # Si no hay nada dinámico, usamos la URL por defecto como último recurso
            pdf_urls = ["https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf"]

        # Probamos las URLs encontradas (empezando por la primera que suele ser la más reciente)
        pdf_path = os.path.join(DATA_DIR, "informe_diario.pdf")
        descargado = False

        for url in pdf_urls:
            print(f"Intentando descargar: {url}")
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code == 200:
                if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
                with open(pdf_path, 'wb') as f:
                    f.write(res.content)
                descargado = True
                print("✅ PDF obtenido con éxito.")
                break
        
        if not descargado:
            print("❌ No se pudo encontrar un PDF válido disponible.")
            return

        # 2. Procesar el PDF
        stocks = []
        with pdfplumber.open(pdf_path) as pdf:
            # Revisamos la primera página
            table = pdf.pages[0].extract_table()
            if table:
                for row in table[1:]:
                    if row and len(row) >= 2 and row[0] and row[1]:
                        ticker = row[0].split('\n')[-1].strip()
                        parts = row[1].split('\n')
                        precio = parts[0].strip() if len(parts) > 0 else "0,00"
                        variacion = parts[1].strip() if len(parts) > 1 else "0,00%"
                        stocks.append({"ticker": ticker, "precio": precio, "variacion": variacion})

        if stocks:
            output = {
                "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
                "stocks": stocks
            }
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=4, ensure_ascii=False)
            print(f"✅ API actualizada: {len(stocks)} acciones encontradas.")
        else:
            print("❌ El PDF no tenía el formato de tabla esperado.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    run()
