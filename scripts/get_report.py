import pdfplumber
import requests
import json
import re
import os
from datetime import datetime

URL = "https://rendivalores.com/assets/pdfs/resumen/resumen-diario-rendivalores.pdf"
DATA_PATH = "data/market_data.json"

def extract_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        print(f"Buscando PDF en: {URL}")
        response = requests.get(URL, headers=headers, timeout=20)
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Error de red: {e}")
        return

    results = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "market_summary": {"dolar_bcv": "0", "ibc_principal": "0", "ind_financiero": "0", "ind_industrial": "0", "volumen_total": "0"},
        "stocks": []
    }

    with pdfplumber.open("temp.pdf") as pdf:
        full_text = ""
        for page in pdf.pages:
            # Extraemos el texto crudo
            text = page.extract_text() or ""
            full_text += text + "\n"
        
        # Muestra en la consola de GitHub qué está leyendo realmente
        print("--- DEBUG: INICIO DEL TEXTO EXTRAÍDO ---")
        print(full_text[:500]) # Solo los primeros 500 caracteres para no saturar
        print("--- DEBUG: FIN DEL TEXTO ---")

        # 1. Resumen de Mercado (Búsqueda por palabras clave ultra-flexible)
        results["market_summary"]["dolar_bcv"] = (re.findall(r"BCV.*?([\d,.]+)", full_text, re.S) + ["0"])[0]
        results["market_summary"]["ibc_principal"] = (re.findall(r"IBC.*?([\d,.]+)", full_text, re.S) + ["0"])[0]
        
        # 2. Monitor de Acciones (Búsqueda de filas de tabla por texto)
        # Este Regex busca: Mayúsculas (Ticker) + Espacio + Número (Precio) + Espacio + Porcentaje (Variación)
        # Ejemplo: BNC 1.250,00 +1,50%
        stock_matches = re.findall(r"([A-Z]{3,6})\s+([\d,.]+)\s+([+-]?[\d,.]+%)\s+([\d,.]+)", full_text)
        
        for m in stock_matches:
            if m[0] not in ["FECHA", "TOTAL", "RIF"]:
                results["stocks"].append({
                    "ticker": m[0],
                    "precio": m[1],
                    "variacion": m[2],
                    "volumen": m[3]
                })

    # Guardado Forzado
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as j:
        json.dump(results, j, indent=4)
    
    if os.path.exists("temp.pdf"): os.remove("temp.pdf")
    print(f"✅ Scraping finalizado. Acciones: {len(results['stocks'])}")

if __name__ == "__main__":
    extract_data()
