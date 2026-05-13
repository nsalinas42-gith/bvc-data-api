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
        response = requests.get(URL, headers=headers, timeout=15)
        with open("temp.pdf", "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"Error descarga: {e}")
        return

    results = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "market_summary": {"dolar_bcv": "0", "ibc_principal": "0", "ind_financiero": "0", "ind_industrial": "0", "volumen_total": "0"},
        "stocks": []
    }

    with pdfplumber.open("temp.pdf") as pdf:
        # 1. Extraemos texto plano solo para el resumen (BCV, IBC)
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"

        # Regex mejorado para capturar solo el número
        results["market_summary"]["dolar_bcv"] = (re.findall(r"BCV\s*([\d,.]+)", full_text) + ["0"])[0]
        results["market_summary"]["ibc_principal"] = (re.findall(r"IBC\s*([\d,.]+)", full_text) + ["0"])[0]
        results["market_summary"]["volumen_total"] = (re.findall(r"Efectivo\s*([\d,.]+)", full_text) + ["0"])[0]

        # 2. Extraemos TABLAS para las acciones
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Una fila válida de acciones suele tener: TICKER, PRECIO, VARIACIÓN, VOLUMEN
                    # Ejemplo: ['BNC', '1.350,00', '+1,20%', '50.000']
                    if row and len(row) >= 3:
                        ticker = str(row[0]).strip()
                        # Validamos que el ticker sea Mayúsculas y de 3 a 6 caracteres
                        if re.match(r"^[A-Z]{3,6}$", ticker):
                            results["stocks"].append({
                                "ticker": ticker,
                                "precio": str(row[1]).strip(),
                                "variacion": str(row[2]).strip(),
                                "volumen": str(row[3]).strip() if len(row) > 3 else "0"
                            })

    # Guardar y limpiar
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as j:
        json.dump(results, j, indent=4)
    
    if os.path.exists("temp.pdf"): os.remove("temp.pdf")
    print(f"✅ Scraping completado. Datos guardados. Acciones: {len(results['stocks'])}")

if __name__ == "__main__":
    extract_data()
