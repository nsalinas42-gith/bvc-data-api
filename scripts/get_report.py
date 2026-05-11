import os
import json
from datetime import datetime

def run():
    # 1. Asegurar que la carpeta existe
    folder = "data"
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Carpeta '{folder}' creada.")

    # 2. Definir la ruta del archivo
    file_path = os.path.join(folder, "market_data.json")

    # 3. Crear datos de prueba mínimos
    test_data = {
        "last_update": datetime.now().strftime("%d/%m/%Y %I:%M %p"),
        "stocks": [
            {"ticker": "TEST", "precio": "100,00", "variacion": "1,50%"}
        ]
    }

    # 4. Intentar escribir el archivo
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f, indent=4)
        print(f"✅ ARCHIVO CREADO EN: {file_path}")
    except Exception as e:
        print(f"❌ ERROR AL ESCRIBIR: {e}")

if __name__ == "__main__":
    run()
