import requests
import json
import os
from datetime import datetime

# Rutas
DATA_DIR = "data"
JSON_PATH = os.path.join(DATA_DIR, "market_data.json")

def run():
    # Crear carpeta si no existe
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Carpeta {DATA_DIR} creada.")

    # Datos de prueba (para asegurar que el archivo se cree)
    data = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "status": "Sistema activo",
        "fuente": "Bolsa de Valores de Caracas"
    }

    # Intentar descargar el PDF real (opcional por ahora para probar)
    try:
        url = "https://rendivalores.com/wp-content/uploads/Informe-de-cierre-diario.pdf"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            with open(os.path.join(DATA_DIR, "informe_diario.pdf"), 'wb') as f:
                f.write(response.content)
            print("PDF guardado.")
    except Exception as e:
        print(f"Aviso: No se pudo descargar el PDF: {e}")

    # Guardar el JSON sí o sí
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)
    
    print(f"Archivo {JSON_PATH} generado exitosamente.")

if __name__ == "__main__":
    run()
