import pdfplumber
import requests
import json
import re
import os
from datetime import datetime

URL = "https://rendivalores.com/assets/pdfs/resumen/resumen-diario-rendivalores.pdf"
DATA_PATH = "data/market_data.json"

def clean_num(text):
    """Limpia el texto para dejar solo el formato numérico."""
    if not text: return "0"
    # Solo permite números, puntos y comas
    found = re.search(r"([\d\.,]+)", text)
    return found.group(1) if found else "0"

def extract_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(URL, headers=headers, timeout=20)
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
    except:
        return

    results = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "market_summary": {"dolar_bcv": "0", "ibc_principal": "0", "ind_financiero": "0", "ind_industrial": "0", "volumen_total": "0"},
        "stocks": []
    }

    with pdfplumber.open("temp.pdf") as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += (page.extract_text() or "") + "\n"
        
        # --- EXTRACCIÓN DE RESUMEN (PRECISIÓN MEJORADA) ---
        
        # 1. Volumen Total: Buscamos después de "volumen total efectivo de BS ."
        vol_match = re.search(r"volumen total efectivo de\s*BS\s*\.\s*([\d\.,]+)", full_text, re.I)
        if vol_match:
            results["market_summary"]["volumen_total"] = vol_match.group(1)

        # 2. IBC: Buscamos "IBC" seguido de un número grande (normalmente > 1.000)
        ibc_match = re.search(r"IBC[:\s]+([\d\.]{5,10},[\d]{2})", full_text)
        if ibc_match:
            results["market_summary"]["ibc_principal"] = ibc_match.group(1)

        # 3. Dólar BCV: Buscamos "BCV" pero evitamos que tome 4 dígitos (como el año 2026)
        # Buscamos específicamente un número con coma decimal (ej: 36,45)
        bcv_match = re.search(r"BCV[:\s]+(\d{2},[\d]{2})", full_text)
        if bcv_match:
            results["market_summary"]["dolar_bcv"] = bcv_match.group(1)

        # --- EXTRACCIÓN DE ACCIONES ---
        # El log mostró: "acciones de BVCC con 16,39%"
        # Vamos a capturar el ticker y la variación.
        stock_finds = re.findall(r"([A-Z]{3,6})\s+con\s+([+-]?[\d,.]+\%)", full_text)
        
        for name, var in stock_finds:
            if name not in ["TOTAL", "BOLSA", "VALOR"]:
                results["stocks"].append({
                    "ticker": name,
                    "precio": "Ver PDF", # Precio no disponible en el texto narrativo
                    "variacion": var,
                    "volumen": "N/A"
                })

    # Guardado
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as j:
        json.dump(results, j, indent=4)
    
    if os.path.exists("temp.pdf"): os.remove("temp.pdf")
    print(f"✅ Proceso finalizado. {len(results['stocks'])} acciones detectadas.")

if __name__ == "__main__":
    extract_data()
