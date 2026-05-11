import requests, pdfplumber, json, os
from datetime import datetime

def run():
    url = "https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf"
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)
        if r.status_code == 200:
            with open("data/informe_diario.pdf", 'wb') as f: f.write(r.content)
            stocks = []
            with pdfplumber.open("data/informe_diario.pdf") as pdf:
                table = pdf.pages[0].extract_table()
                if table:
                    for row in table[1:]:
                        if row[0] and row[1]:
                            stocks.append({
                                "ticker": row[0].split('\n')[-1],
                                "precio": row[1].split('\n')[0],
                                "variacion": row[1].split('\n')[1] if '\n' in row[1] else "0,00%"
                            })
            output = {"last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"), "stocks": stocks}
            with open("data/market_data.json", 'w', encoding='utf-8') as f:
                json.dump(output, f, indent=4)
            print(f"Éxito: {len(stocks)} acciones.")
    except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    if not os.path.exists('data'): os.makedirs('data')
    run()
