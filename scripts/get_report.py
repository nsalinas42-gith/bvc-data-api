import requests
import pdfplumber
import json
import os
from datetime import datetime

DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def run():
    # Añadimos un parámetro aleatorio al final (?v=...) para romper la caché del servidor
    timestamp = int(datetime.now().timestamp())
    url = f"https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf?v={timestamp}"
    
    # Cabeceras que imitan a un navegador Chrome real para evitar bloqueos
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/pdf',
        'Referer': 'https://rendivalores.com/'
    }
    
    try:
        print(f"Intentando descarga forzada desde: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
            pdf_path = os.path.join(DATA_DIR, "informe_diario.pdf")
            
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            print("✅ PDF descargado. Iniciando extracción de datos...")
            
            stocks = []
            with pdfplumber.open(pdf_path) as pdf:
                # Buscamos la tabla en las primeras 2 páginas por si acaso se movió
                for page in pdf.pages[:2]:
                    table = page.extract_table()
                    if table:
                        for row in table[1:]:
                            if row and row[0] and row[1]:
                                ticker = row[0].split('\n')[-1].strip()
                                # Limpieza de precios y variaciones
                                parts = row[1].split('\n')
                                precio = parts[0].strip() if len(parts) > 0 else "0,00"
                                variacion = parts[1].strip() if len(parts) > 1 else "0,00%"
                                stocks.append({"ticker": ticker, "precio": precio, "variacion": variacion})
                        if stocks: break # Si encontramos datos, paramos de buscar

            if stocks:
                output = {
                    "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
                    "stocks": stocks
                }
                with open(JSON_PATH, "w", encoding="utf-8") as f:
                    json.dump(output, f, indent=4, ensure_ascii=False)
                print(f"✅ ¡Éxito! {len(stocks)} acciones procesadas.")
            else:
                print("❌ Se descargó el PDF pero no se encontró la tabla de datos.")
                
        else:
            print(f"❌ Error {response.status_code}: El servidor sigue bloqueando el acceso.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    run()
