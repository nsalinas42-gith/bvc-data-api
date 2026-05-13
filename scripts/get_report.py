import pdfplumber
import requests
import json
import re
import os
from datetime import datetime

URL = "https://rendivalores.com/assets/pdfs/resumen/resumen-diario-rendivalores.pdf"
DATA_PATH = "data/market_data.json"

def clean_text(text):
    # Elimina múltiples espacios y saltos de línea para facilitar el Regex
    return " ".join(text.split())

def safe_extract(pattern, text, default="0"):
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).replace(".", "X").replace(",", ".").replace("X", ",").strip() # Normaliza formato si quieres, o déjalo igual
    return default

def extract_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
    except:
        return

    results = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "market_summary": {},
        "stocks": []
    }

    with pdfplumber.open("temp.pdf") as pdf:
        # Extraemos texto de TODAS las páginas y lo limpiamos
        raw_text = ""
        for page in pdf.pages:
            raw_text += page.extract_text() + " "
        
        full_text = clean_text(raw_text)
        
        # --- EXTRACCIÓN AGRESIVA ---
        # Buscamos el valor numérico más cercano a la palabra clave
        results["market_summary"] = {
            "dolar_bcv": safe_extract(r"BCV\s*[:\s]*([\d,.]+)", full_text),
            "ibc_principal": safe_extract(r"IBC\s*[:\s]*([\d,.]+)", full_text),
            "ind_financiero": safe_extract(r"Financiero\s*[:\s]*([\d,.]+)", full_text),
            "ind_industrial": safe_extract(r"Industrial\s*[:\s]*([\d,.]+)", full_text),
            "volumen_total": safe_extract(r"Efectivo\s*[:\s]*([\d,.]+)", full_text)
        }

        # --- EXTRACCIÓN DE ACCIONES ---
        # Buscamos: Letras Mayúsculas (Ticker) + Precio + Variación (%)
        # Ejemplo: "BNC 1.350,00 +1,20%"
        stock_matches = re.findall(r"([A-Z]{3,6})\s+([\d,.]+)\s+([+-]?[\d,.]+%)\s+([\d,.]+)", full_text)
        
        seen = set()
        for m in stock_matches:
            ticker = m[0]
            if ticker not in ["TOTAL", "MONTO", "RESUMEN"] and ticker not in seen:
                results["stocks"].append({
                    "ticker": ticker,
                    "precio": m[1],
                    "variacion": m[2],
                    "volumen": m[3]
                })
                seen.add(ticker)

    # Guardar
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as j:
        json.dump(results, j, indent=4)
    
    if os.path.exists("temp.pdf"): os.remove("temp.pdf")
    print(f"✅ Scraping completado. Acciones encontradas: {len(results['stocks'])}")

if __name__ == "__main__":
    extract_data()
