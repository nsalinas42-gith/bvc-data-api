import pdfplumber
import requests
import json
import re
import os
from datetime import datetime

# URL del PDF (según el hallazgo en la sesión técnica)
URL = "https://rendivalores.com/assets/pdfs/resumen/resumen-diario-rendivalores.pdf"
DATA_PATH = "data/market_data.json"

def extract_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    response = requests.get(URL, headers=headers)
    
    with open("temp.pdf", "wb") as f:
        f.write(response.content)

    results = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "market_summary": {},
        "stocks": []
    }

    with pdfplumber.open("temp.pdf") as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text()

        # --- Extracción de Indicadores Globales ---
        # Ejemplo de Regex para capturar valores (ajustar según el texto exacto del PDF)
        results["market_summary"]["dolar_bcv"] = re.search(r"Dólar BCV[:\s]+([\d,.]+)", full_text).group(1) if re.search(r"Dólar BCV", full_text) else "N/A"
        results["market_summary"]["ibc_principal"] = re.search(r"IBC[:\s]+([\d,.]+)", full_text).group(1) if re.search(r"IBC", full_text) else "N/A"
        results["market_summary"]["volumen_total"] = re.search(r"Volumen Total[:\s]+([\d,.]+)", full_text).group(1) if re.search(r"Volumen Total", full_text) else "0"

        # --- Monitor de Acciones (Regex Flexible) ---
        # Buscamos patrones como: TICKER PRECIO VARIACION VOLUMEN
        # Ejemplo: BNC 1.350,00 +1,20% 500.000
        stock_pattern = re.compile(r"([A-Z]{3,5})\s+([\d,.]+)\s+([+-]?[\d,.]+%)\s+([\d,.]+)")
        matches = stock_pattern.findall(full_text)

        for match in matches:
            results["stocks"].append({
                "ticker": match[0],
                "precio": match[1],
                "variacion": match[2],
                "volumen": match[3]
            })

    # Asegurar que la carpeta data existe
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    with open(DATA_PATH, "w") as j:
        json.dump(results, j, indent=4)
    
    print(f"✅ Datos guardados exitosamente en {DATA_PATH}")

if __name__ == "__main__":
    extract_data()
