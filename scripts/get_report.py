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
        response = requests.get(URL, headers=headers, timeout=20)
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Error de red: {e}")
        return

    results = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "market_summary": {
            "dolar_bcv": "0",
            "ibc_principal": "0",
            "ind_financiero": "0",
            "ind_industrial": "0",
            "volumen_total": "0"
        },
        "stocks": []
    }

    with pdfplumber.open("temp.pdf") as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"
        
        # --- EXTRACCIÓN DE RESUMEN ---
        # Buscamos el volumen total basándonos en tu log: "volumen total efectivo de BS . 1.706.982.681,50"
        vol_match = re.search(r"volumen total efectivo de\s*BS\s*\.\s*([\d,.]+)", full_text, re.IGNORECASE)
        if vol_match:
            results["market_summary"]["volumen_total"] = vol_match.group(1)

        # Para el IBC y Dólar BCV (suelen estar en otra parte del texto)
        results["market_summary"]["dolar_bcv"] = (re.findall(r"BCV[:\s]+([\d,.]+)", full_text) + ["0"])[0]
        results["market_summary"]["ibc_principal"] = (re.findall(r"IBC[:\s]+([\d,.]+)", full_text) + ["0"])[0]

        # --- EXTRACCIÓN DE ACCIONES (TOP RENDIMIENTO) ---
        # Basado en tu log: "acciones de BVCC con 16,39%" o "BNC con 0,73%"
        # Buscamos: Siglas (3-5 letras) + " con " + Porcentaje
        stock_finds = re.findall(r"([A-Z]{3,6})\s+con\s+([\d,.]+\%)", full_text)
        
        for name, var in stock_finds:
            results["stocks"].append({
                "ticker": name,
                "precio": "Ver PDF", # El precio no aparece directo en el texto narrativo
                "variacion": var,
                "volumen": "Consultar"
            })

    # Guardado
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as j:
        json.dump(results, j, indent=4)
    
    if os.path.exists("temp.pdf"): os.remove("temp.pdf")
    print(f"✅ Scraping finalizado. Acciones detectadas: {len(results['stocks'])}")

if __name__ == "__main__":
    extract_data()
