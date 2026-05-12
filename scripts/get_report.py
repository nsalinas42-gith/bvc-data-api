import requests
import pdfplumber
import json
import os
from datetime import datetime

DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def run():
    # La URL exacta que encontraste manualmente
    url = "https://rendivalores.com/assets/pdfs/resumen/resumen-diario-rendivalores.pdf"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/pdf'
    }
    
    try:
        print(f"Descargando PDF desde la ruta de activos: {url}")
        # Añadimos un pequeño truco de tiempo para evitar que el servidor nos dé una versión vieja
        response = requests.get(f"{url}?t={int(datetime.now().timestamp())}", headers=headers, timeout=25)
        
        if response.status_code == 200:
            if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
            pdf_path = os.path.join(DATA_DIR, "informe_diario.pdf")
            
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            print("✅ PDF descargado. Procesando tabla de acciones...")
            
            stocks = []
            with pdfplumber.open(pdf_path) as pdf:
                # Intentamos extraer la tabla de la página 1
                table = pdf.pages[0].extract_table()
                
                if table:
                    for row in table:
                        # Buscamos filas que parezcan datos de mercado
                        # Usualmente: [Ticker, Precio, Variación...]
                        if row and len(row) >= 2:
                            ticker = str(row[0]).strip()
                            # Validamos que el ticker sea corto y en mayúsculas (como BNC, BPV, etc.)
                            if ticker and ticker.isupper() and len(ticker) <= 6:
                                try:
                                    # Limpiamos el precio y la variación
                                    # A veces vienen en la misma celda o celdas separadas
                                    precio = str(row[1]).split('\n')[0].strip()
                                    variacion = "0,00%"
                                    if '\n' in str(row[1]):
                                        variacion = str(row[1]).split('\n')[1].strip()
                                    elif len(row) > 2 and row[2]:
                                        variacion = str(row[2]).strip()
                                        
                                    stocks.append({
                                        "ticker": ticker,
                                        "precio": precio,
                                        "variacion": variacion
                                    })
                                except:
                                    continue

            if stocks:
                output = {
                    "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
                    "fuente": "Bolsa de Valores de Caracas (vía Rendivalores)",
                    "stocks": stocks
                }
                with open(JSON_PATH, "w", encoding="utf-8") as f:
                    json.dump(output, f, indent=4, ensure_ascii=False)
                print(f"✅ ¡API lista! Se encontraron {len(stocks)} acciones.")
            else:
                print("❌ No se detectaron acciones en el formato esperado dentro del PDF.")
        else:
            print(f"❌ Error {response.status_code} al acceder al PDF.")

    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    run()
