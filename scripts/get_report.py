import pdfplumber
import requests
import json
import re
import os
from datetime import datetime

# URL del PDF (según el hallazgo en la sesión técnica)
URL = "https://rendivalores.com/assets/pdfs/resumen/resumen-diario-rendivalores.pdf"
DATA_PATH = "data/market_data.json"

def safe_extract(pattern, text, default="N/A"):
    """Busca un patrón y devuelve el grupo 1, si no existe devuelve el default."""
    match = re.search(pattern, text)
    if match:
        try:
            return match.group(1)
        except IndexError:
            return default
    return default

def extract_data():
    # ... (código anterior de descarga y apertura del PDF)
    
    with pdfplumber.open("temp.pdf") as pdf:
        full_text = ""
        for page in pdf.pages:
            # Forzamos la extracción de texto para que sea más limpia
            full_text += page.extract_text(layout=True) + "\n"

        # --- Extracción de Indicadores con el nuevo método seguro ---
        # El patrón [\d,.]+ busca números con puntos y comas
        results["market_summary"] = {
            "dolar_bcv": safe_extract(r"BCV[:\s]+([\d,.]+)", full_text),
            "ibc_principal": safe_extract(r"IBC[:\s]+([\d,.]+)", full_text),
            "ind_financiero": safe_extract(r"Financiero[:\s]+([\d,.]+)", full_text),
            "ind_industrial": safe_extract(r"Industrial[:\s]+([\d,.]+)", full_text),
            "volumen_total": safe_extract(r"Efectivo\s+Varios[:\s]+([\d,.]+)", full_text)
        }

        # --- Monitor de Acciones ---
        # Ajustamos el regex para que sea más tolerante a espacios y saltos de línea
        stock_pattern = re.compile(r"([A-Z]{3,6})\s+([\d,.]+)\s+([+-]?[\d,.]+%)\s+([\d,.]+)")
        matches = stock_pattern.findall(full_text)
        
        # Limpiamos duplicados o basura si es necesario
        for match in matches:
            results["stocks"].append({
                "ticker": match[0],
                "precio": match[1],
                "variacion": match[2],
                "volumen": match[3]
            })

    # Guardado del archivo (se mantiene igual)
    # ...
    # Asegurar que la carpeta data existe
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    with open(DATA_PATH, "w") as j:
        json.dump(results, j, indent=4)
    
    print(f"✅ Datos guardados exitosamente en {DATA_PATH}")

if __name__ == "__main__":
    extract_data()
