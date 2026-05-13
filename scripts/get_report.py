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

        # --- Extracción de Indicadores con Regex más flexibles ---
        # Buscamos el número que sigue a la palabra clave, ignorando símbolos intermedios
        results["market_summary"] = {
            # Busca 'BCV' y captura el primer número con formato decimal (ej: 36,45)
            "dolar_bcv": safe_extract(r"BCV.*?([\d,.]+)", full_text),
            
            # Busca 'IBC' o 'Índice Principal' y captura el número
            "ibc_principal": safe_extract(r"IBC.*?([\d,.]+)", full_text),
            
            # Busca índices específicos
            "ind_financiero": safe_extract(r"Financiero.*?([\d,.]+)", full_text),
            "ind_industrial": safe_extract(r"Industrial.*?([\d,.]+)", full_text),
            
            # El volumen total suele estar tras etiquetas como 'Efectivo' o 'Monto'
            "volumen_total": safe_extract(r"(?:Total Negociado|Efectivo).*?([\d,.]+)", full_text)
        }

        # --- Monitor de Acciones (Regex mejorado para columnas de tabla) ---
        # Buscamos el Ticker (3-5 letras) seguido de números y porcentajes
        # Ejemplo: ABC 1.234,56 +1,20% 10.000
        stock_pattern = re.compile(r"([A-Z]{3,6})\s+([\d,.]+)\s+([+-]?[\d,.]+%)\s+([\d,.]+)")
        matches = stock_pattern.findall(full_text)

        seen_tickers = set()
        for match in matches:
            ticker = match[0]
            # Evitamos duplicar tickers o capturar cabeceras de tabla
            if ticker not in ["FECHA", "HORA", "MONTO"] and ticker not in seen_tickers:
                results["stocks"].append({
                    "ticker": ticker,
                    "precio": match[1],
                    "variacion": match[2],
                    "volumen": match[3]
                })
                seen_tickers.add(ticker)

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
