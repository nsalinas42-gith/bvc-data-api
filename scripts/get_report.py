import pdfplumber
import requests
import json
import re
import os
from datetime import datetime

URL = "https://rendivalores.com/assets/pdfs/resumen/resumen-diario-rendivalores.pdf"
DATA_PATH = "data/market_data.json"
TEMP_PDF = "temp.pdf"

def safe_extract(pattern, text, default="0"):
    """Busca un patrón y devuelve el grupo 1 de forma segura."""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return default

def extract_data():
    print(f"📥 Descargando reporte desde: {URL}")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status() # Lanza error si la descarga falla (404, 500, etc)
        with open(TEMP_PDF, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"❌ Error descargando el PDF: {e}")
        return

    results = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "market_summary": {},
        "stocks": []
    }

    if not os.path.exists(TEMP_PDF):
        print("❌ Error: El archivo temp.pdf no se encontró después de la descarga.")
        return

    with pdfplumber.open(TEMP_PDF) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

        # --- Extracción de Indicadores (Ajustado al formato Rendivalores) ---
        # Usamos nombres clave que suelen aparecer en el PDF
        results["market_summary"] = {
            "dolar_bcv": safe_extract(r"BCV[:\s]+([\d,.]+)", full_text),
            "ibc_principal": safe_extract(r"IBC[:\s]+([\d,.]+)", full_text),
            "ind_financiero": safe_extract(r"Financiero[:\s]+([\d,.]+)", full_text),
            "ind_industrial": safe_extract(r"Industrial[:\s]+([\d,.]+)", full_text),
            "volumen_total": safe_extract(r"Efectivo\s+Varios[:\s]+([\d,.]+)", full_text)
        }

        # --- Monitor de Acciones (17 acciones comunes) ---
        # Este regex captura: TICKER | PRECIO | VARIACIÓN | VOLUMEN
        stock_pattern = re.compile(r"([A-Z]{3,6})\s+([\d,.]+)\s+([+-]?[\d,.]+%)\s+([\d,.]+)")
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
    
    print(f"✅ Proceso finalizado. {len(results['stocks'])} acciones procesadas.")
    
    # Limpieza
    if os.path.exists(TEMP_PDF):
        os.remove(TEMP_PDF)

if __name__ == "__main__":
    extract_data()
