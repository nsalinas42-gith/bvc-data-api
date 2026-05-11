import requests
import pdfplumber
import json
import os
from datetime import datetime

# Configuración de rutas
DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def download_pdf():
    # URL oficial del informe diario de la BVC a través de Rendivalores
    url = "https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
            with open(os.path.join(DATA_DIR, "informe_diario.pdf"), 'wb') as f:
                f.write(response.content)
            return True
        return False
    except Exception as e:
        print(f"Error descargando PDF: {e}")
        return False

def extract_data():
    try:
        stocks = []
        pdf_path = os.path.join(DATA_DIR, "informe_diario.pdf")
        
        with pdfplumber.open(pdf_path) as pdf:
            # Buscamos en la primera página donde suele estar la tabla de acciones
            table = pdf.pages[0].extract_table()
            if table:
                # Saltamos la cabecera e iteramos las filas
                for row in table[1:]:
                    # Validamos que la fila tenga el formato esperado (Ticker, Precio, Var)
                    if row[0] and row[1]:
                        # Limpieza básica de nombres si vienen con saltos de línea
                        ticker = row[0].split('\n')[-1] if '\n' in row[0] else row[0]
                        stocks.append({
                            "ticker": ticker,
                            "precio": row[1].split('\n')[0] if row[1] else "0,00",
                            "variacion": row[1].split('\n')[1] if row[1] and '\n' in row[1] else "0,00%"
                        })

        # Estructura final que espera tu Dashboard de React
        output = {
            "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
            "fuente": "Bolsa de Valores de Caracas",
            "stocks": stocks
        }

        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=4, ensure_ascii=False)
        
        print(f"✅ JSON generado con {len(stocks)} acciones.")

    except Exception as e:
        print(f"❌ Error extrayendo datos: {e}")

if __name__ == "__main__":
    if download_pdf():
        extract_data()
    else:
        print("No se pudo obtener el PDF de hoy.")
