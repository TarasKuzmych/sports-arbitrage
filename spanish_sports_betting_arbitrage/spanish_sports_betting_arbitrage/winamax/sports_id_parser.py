from bs4 import BeautifulSoup
import json
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

ruta_archivo = ROOT_DIR / 'winamax/winamax.html'

archivo_resultados = ROOT_DIR / 'winamax/sports_id_winamax.txt'

with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
    html_content = archivo.read()

soup = BeautifulSoup(html_content, 'html.parser')
script_tags = soup.find_all('script', {'type': 'text/javascript'})

preloaded_state = None

for script in script_tags:
    if 'PRELOADED_STATE' in script.text:
        json_str = script.text.split('=', 1)[1].strip()
        json_str = json_str.rstrip(';')
        try:
            preloaded_state = json.loads(json_str)
            break
        except json.decoder.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")

if preloaded_state:
    print("JSON data extracted successfully!")
    # Example of processing the data:
    sports_data = preloaded_state.get('sports', {})
    
    with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        for sport_id, sport_details in sports_data.items():
            sport_name = sport_details.get('sportName', 'Unknown')
            archivo_salida.write(f"Sport ID: {sport_id}, Sport Name: {sport_name}\n")
            # Further processing and writing to file...
else:
    print("PRELOADED_STATE not found in the HTML.")
