import requests
import pdfplumber
import json
import os
from datetime import datetime

DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def run():
    # Intentamos varias opciones de URL por si cambiaron el nombre hoy
    hoy = datetime.now().strftime("%d%m%Y") # Ejemplo: 11052026
    urls_a_probar = [
        "https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf",
        f"https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario-{hoy}.pdf",
        "https://rendivalores.com/wp-content/uploads/Resumen-de-Mercado.pdf"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    pdf_descargado = False
    
    for url in urls_a_probar:
        try:
            print(f"Probando: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
                with open(os.path.join(DATA_DIR, "informe_diario.pdf"), 'wb') as f:
                    f.write(response.content)
                pdf_descargado = True
                print("✅ ¡PDF Encontrado!")
                break
        except:
            continue

    if not pdf_descargado:
        print("❌ Ninguna URL funcionó. Es posible que el reporte de hoy aún no se haya subido.")
        return

    # Si llegó aquí, procesamos el PDF
    try:
        stocks = []
        with pdfplumber.open(os.path.join(DATA_DIR, "informe_diario.pdf")) as pdf:
            table = pdf.pages[0].extract_table()
            if table:
                for row in table[1:]:
                    if row and row[0] and row[1]:
                        ticker = row[0].split('\n')[-1].strip()
                        parts = row[1].split('\n')
                        precio = parts[0].strip() if len(parts) > 0 else "0,00"
                        variacion = parts[1].strip() if len(parts) > 1 else "0,00%"
                        stocks.append({"ticker": ticker, "precio": precio, "variacion": variacion})

        output = {
            "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
            "stocks": stocks
        }
        
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        print(f"✅ JSON actualizado con {len(stocks)} acciones.")

    except Exception as e:
        print(f"❌ Error procesando PDF: {e}")

if __name__ == "__main__":
    run()
