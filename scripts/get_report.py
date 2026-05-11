import requests
import pdfplumber
import json
import os
from datetime import datetime

PDF_PATH = "data/informe_diario.pdf"
JSON_PATH = "data/market_data.json"

def download_pdf():
    url = "https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            with open(PDF_PATH, 'wb') as f:
                f.write(response.content)
            return True
        return False
    except:
        return False

def extract_data():
    try:
        stocks = []
        with pdfplumber.open(PDF_PATH) as pdf:
            table = pdf.pages[0].extract_table()
            if table:
                for row in table[1:]:
                    if row[0]:
                        stocks.append({
                            "ticker": row[0].split('\n')[-1] if '\n' in row[0] else row[0],
                            "precio": row[1].split('\n')[0] if row[1] else "0",
                            "variacion": row[1].split('\n')[1] if row[1] and '\n' in row[1] else "0.00%"
                        })
        output = {"last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"), "stocks": stocks}
        with open(JSON_PATH, 'w') as f:
            json.dump(output, f, indent=4)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if not os.path.exists('data'): os.makedirs('data')
    if download_pdf(): extract_data()
