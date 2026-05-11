import requests
import pdfplumber
import json
import os
from datetime import datetime

# Configuración de rutas
DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def run():
    # URL oficial del informe de Rendivalores
    url = "https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        print("Iniciando descarga del PDF...")
        response = requests.get(url, headers=headers, timeout=25)
        
        if response.status_code == 200:
            if not os.path.exists(DATA_DIR):
                os.makedirs(DATA_DIR)
            
            pdf_path = os.path.join(DATA_DIR, "informe_diario.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            
            stocks = []
            with pdfplumber.open(pdf_path) as pdf:
                # Extraemos la tabla de la primera página
                table = pdf.pages[0].extract_table()
                if table:
                    # Filtramos filas vacías y saltamos el encabezado
                    for row in table[1:]:
                        if row and row[0] and row[1]:
                            # Limpieza de Ticker (maneja posibles saltos de línea)
                            ticker = row[0].split('\n')[-1].strip()
                            
                            # Separar Precio y Variación (suelen venir en la misma celda)
                            parts = row[1].split('\n')
                            precio = parts[0].strip() if len(parts) > 0 else "0,00"
                            variacion = parts[1].strip() if len(parts) > 1 else "0,00%"
                            
                            stocks.append({
                                "ticker": ticker,
                                "precio": precio,
                                "variacion": variacion
                            })
            
            # Guardamos el resultado final
            output = {
                "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
                "stocks": stocks
            }
            
            with open(JSON_PATH, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=4, ensure_ascii=False)
            
            print(f"✅ Éxito: Se extrajeron {len(stocks)} acciones reales.")
        else:
            print(f"❌ Error al descargar: Código {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error crítico: {e}")

if __name__ == "__main__":
    run()
