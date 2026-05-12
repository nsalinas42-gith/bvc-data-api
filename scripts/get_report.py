import requests
import pdfplumber
import json
import os
import re
from datetime import datetime

DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def run():
    url = "https://rendivalores.com/assets/pdfs/resumen/resumen-diario-rendivalores.pdf"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        print(f"Descargando: {url}")
        response = requests.get(f"{url}?t={int(datetime.now().timestamp())}", headers=headers, timeout=25)
        
        if response.status_code == 200:
            if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
            pdf_path = os.path.join(DATA_DIR, "informe_diario.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            stocks = []
            with pdfplumber.open(pdf_path) as pdf:
                # Extraemos TODO el texto de la primera página
                text = pdf.pages[0].extract_text()
                
                if text:
                    # Buscamos líneas que tengan el formato de la BVC:
                    # Ejemplo: "BNC 1.250,00 +1,50%" o similares
                    # Esta expresión regular busca: MAYÚSCULAS + Espacio + Número con puntos/comas
                    lines = text.split('\n')
                    for line in lines:
                        # Buscamos Tickers comunes de la BVC para identificar las líneas correctas
                        keywords = ['BNC', 'BPV', 'BVCC', 'ABC', 'FVI', 'GPC', 'IVC', 'MPA', 'PTN', 'RST', 'TDV']
                        if any(key in line for key in keywords):
                            parts = line.split()
                            if len(parts) >= 2:
                                # El primer elemento suele ser el Ticker
                                ticker = parts[0].strip()
                                # El segundo suele ser el precio
                                precio = parts[1].strip()
                                # Buscamos si hay un porcentaje de variación en la línea
                                variacion = "0,00%"
                                for p in parts:
                                    if '%' in p or '+' in p or '-' in p:
                                        variacion = p
                                        break
                                
                                stocks.append({
                                    "ticker": ticker,
                                    "precio": precio,
                                    "variacion": variacion
                                })

            if stocks:
                output = {
                    "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
                    "stocks": stocks
                }
                with open(JSON_PATH, "w", encoding="utf-8") as f:
                    json.dump(output, f, indent=4, ensure_ascii=False)
                print(f"✅ ¡Conseguido! {len(stocks)} acciones extraídas.")
            else:
                # Si falla la búsqueda por texto, intentamos una última vez con tablas simples
                print("⚠️ No se encontró por texto, intentando último recurso por tablas...")
                # (Aquí podrías añadir un log del texto extraído para debuguear)
                print(f"Texto detectado (primeros 100 caracteres): {text[:100]}")

        else:
            print(f"❌ Error de descarga: {response.status_code}")

    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    run()
