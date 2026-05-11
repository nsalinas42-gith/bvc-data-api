import requests
import pdfplumber
import json
import os
from datetime import datetime

# Definición de rutas
DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def run_scraper():
    url = "https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        print(f"Descargando PDF desde: {url}")
        response = requests.get(url, headers=headers, timeout=25)
        
        if response.status_code == 200:
            if not os.path.exists(DATA_DIR): 
                os.makedirs(DATA_DIR)
            
            pdf_file = os.path.join(DATA_DIR, "informe_diario.pdf")
            with open(pdf_file, 'wb') as f:
                f.write(response.content)
            
            stocks = []
            with pdfplumber.open(pdf_file) as pdf:
                # Extraemos la tabla de la primera página
                table = pdf.pages[0].extract_table()
                if table:
                    # Saltamos la primera fila (encabezados)
                    for row in table[1:]:
                        if row and row[0] and row[1]:
                            # Ticker: Limpiamos saltos de línea
                            ticker = row[0].split('\n')[-1].strip() if '\n' in row[0] else row[0].strip()
                            # Precio y Variación: Suelen venir juntos en la segunda columna
                            parts = row[1].split('\n')
                            precio = parts[0].strip() if len(parts) > 0 else "0,00"
                            variacion = parts[1].strip() if len(parts) > 1 else "0,00%"
                            
                            stocks.append({
                                "ticker": ticker,
                                "precio": precio,
                                "variacion": variacion
                            })
            
            # Generamos el JSON con la estructura que React espera
            output = {
                "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
                "fuente": "Bolsa de Valores de Caracas",
                "stocks": stocks
            }
            
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Éxito: Se procesaron {len(stocks)} acciones.")
        else:
            print(f"❌ Error: El servidor respondió con código {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error crítico: {str(e)}")

if __name__ == "__main__":
    run_scraper()
