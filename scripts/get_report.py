import requests
import pdfplumber
import json
import os
from datetime import datetime

DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def run():
    url = "https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
            with open(os.path.join(DATA_DIR, "informe_diario.pdf"), 'wb') as f:
                f.write(response.content)
            
            stocks = []
            with pdfplumber.open(os.path.join(DATA_DIR, "informe_diario.pdf")) as pdf:
                table = pdf.pages[0].extract_table()
                if table:
                    for row in table[1:]:
                        if row[0] and row[1]:
                            # Limpieza de datos del PDF
                            ticker = row[0].split('\n')[-1] if '\n' in row[0] else row[0]
                            stocks.append({
                                "ticker": ticker,
                                "precio": row[1].split('\n')[0],
                                "variacion": row[1].split('\n')[1] if '\n' in row[1] else "0,00%"
                            })
            
            output = {
                "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
                "stocks": stocks
            }
            
            with open(JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=4, ensure_ascii=False)
            print(f"Éxito: {len(stocks)} acciones extraídas.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run()
