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
    except:
        return

    results = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "market_summary": {"dolar_bcv": "0", "ibc_principal": "0", "ind_financiero": "0", "ind_industrial": "0", "volumen_total": "0"},
        "stocks": []
    }

    with pdfplumber.open("temp.pdf") as pdf:
        full_text = ""
        seen_tickers = set()

        for page in pdf.pages:
            # 1. Extraer texto para el resumen
            content = page.extract_text() or ""
            full_text += content + "\n"

            # 2. Intentar extraer tablas para el Monitor de Acciones completo
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Buscamos filas que tengan un Ticker (letras), un Precio y una Variación
                    if row and len(row) >= 3:
                        ticker = str(row[0]).strip().upper()
                        # Validamos que sea un ticker real (3-6 letras) y no hayamos guardado ya
                        if re.match(r"^[A-Z]{3,6}$", ticker) and ticker not in ["TOTAL", "BOLSA", "VALOR", "RIF"] and ticker not in seen_tickers:
                            results["stocks"].append({
                                "ticker": ticker,
                                "precio": str(row[1]).strip(),
                                "variacion": str(row[2]).strip(),
                                "volumen": str(row[3]).strip() if len(row) > 3 else "N/A"
                            })
                            seen_tickers.add(ticker)

        # --- RELLENO DE EMERGENCIA (Si las tablas fallan, usar el texto narrativo) ---
        if len(results["stocks"]) < 5:
            stock_finds = re.findall(r"([A-Z]{3,6})\s+con\s+([+-]?[\d,.]+\%)", full_text)
            for name, var in stock_finds:
                if name not in seen_tickers:
                    results["stocks"].append({"ticker": name, "precio": "Ver PDF", "variacion": var, "volumen": "N/A"})
                    seen_tickers.add(name)

        # --- RESUMEN DE MERCADO ---
        # BCV (Busca número con coma: 36,45)
        bcv = re.search(r"BCV[:\s]+(\d+,\d{2})", full_text)
        results["market_summary"]["dolar_bcv"] = bcv.group(1) if bcv else "Consultar"
        
        # IBC (Busca número largo con decimales)
        ibc = re.search(r"IBC[:\s]+([\d\.,]+)", full_text)
        results["market_summary"]["ibc_principal"] = ibc.group(1) if ibc else "N/A"
        
        # Volumen Total
        vol = re.search(r"volumen total efectivo de\s*BS\s*\.\s*([\d\.,]+)", full_text, re.I)
        results["market_summary"]["volumen_total"] = vol.group(1) if vol else "0"

    # Guardado
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w") as j:
        json.dump(results, j, indent=4)
    
    if os.path.exists("temp.pdf"): os.remove("temp.pdf")
    print(f"✅ Finalizado. Acciones: {len(results['stocks'])}. BCV: {results['market_summary']['dolar_bcv']}")

if __name__ == "__main__":
    extract_data()
