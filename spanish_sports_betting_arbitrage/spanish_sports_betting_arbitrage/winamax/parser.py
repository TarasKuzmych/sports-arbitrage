from bs4 import BeautifulSoup
import json
import unicodedata
import re
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('ASCII')


def clean_name(name):
    # Remove all text within parentheses including the parentheses
    name = re.sub(r'\(.*?\)', '', name)

    name = remove_accents(name)

    # List of prefixes and suffixes to remove
    to_remove = ['KK', 'FC', 'CF', 'CD', 'EC', 'SE', 'MG', 'FK', 'KF', 'AC', 'BK', 'TC', 'NK', 'SD', 'RJ', 'MT', 'BA', 'GO', 'SP', 'CE', 'SC', 'SV', 'RC', 'GC', 'AS', 'SS', 'UD', 'SK', 'CA', 'SL', 'AFC', 'CSC', 'BSC', 'RSC', 'GFC', 'LFC', 'SFC', 'RFC', 'VfL', 'VfB', 'FSV', 'SVW', 'JFC', 'DFC', 'HFC', 'Utd', 'SV', 'RCD', 'FBC', 'PFC', 'TSV', 'EFC', 'CFC', 'BFC', 'JSC', 'OSC', 'RRC', 'CSC', 'GSC', 'HSC', 'MSC', 'SSC', 'VSC', 'WSC', 'ZSC', 'AZ', 'PSV', 'FCZ', 'FCS', 'FCT', 'RKC', 'NAC', 'VVV', 'PEC', 'FCM', 'US', 'AJA', 'AZ', 'RBC', 'TFC', 'WFC', 'IFK', 'GIF', 'BIF', 'AIF', 'MFF', 'AIK', 'DIF', 'HIF', 'ÖFK', 'ÖSK', 'ÖIS', 'GIF', 'AaB', 'BIF', 'FCK', 'OB', 'VB', 'AGF', 'RFC', 'JJK', 'HJK', 'HIFK', 'SJK', 'KTP', 'KPV', 'PS', 'KuPS', 'MYPA', 'VPS', 'FF', 'IF', 'IK', 'BKV', 'BSV', 'B1901', 'B1903', 'B1909', 'B1913', 'KB', 'AB', 'VB', 'LFC', 'BC', 'CB', 'Lfc']

    # Modify the name by removing prefixes and suffixes at the beginning or end
    for item in to_remove:
        # Regular expression for prefix or suffix as a separate word
        word_pattern = r'\b' + re.escape(item) + r'\b'
        name = re.sub(word_pattern, '', name, flags=re.IGNORECASE)

    # Trim and remove extra spaces
    name = ' '.join(name.split())
    return name


ruta_archivo = ROOT_DIR / 'winamax/winamax.html'
archivo_resultados = ROOT_DIR / 'winamax/winamax.txt'

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
    
    matches_data = preloaded_state.get('matches', {})
    bets_data = preloaded_state.get('bets', {})
    outcomes_data = preloaded_state.get('outcomes', {})
    odds_data = preloaded_state.get('odds', {})
    
    with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        for match_id, match_info in matches_data.items():
            if match_info.get('status') == 'PREMATCH':
                teams = match_info.get('title', 'Unknown Match').split(' - ')
                teams = [clean_name(team) for team in teams]

                if len(teams) != 2:
                    continue  # Skip if not exactly two teams

                main_bet_id = match_info.get('mainBetId')
                bet_info = bets_data.get(str(main_bet_id), {})
                outcome_ids = bet_info.get('outcomes', [])

                # Check if odds are available for this match
                odds_available = any(odds_data.get(str(outcome_id)) for outcome_id in outcome_ids)

                if odds_available:
                    archivo_salida.write(f"{teams[0]} - {teams[1]}\n")
                    for i, outcome_id in enumerate(outcome_ids, start=1):
                        odds_value = odds_data.get(str(outcome_id), 'No odds available')
                        archivo_salida.write(f"  {i}: {odds_value}\n")
                    archivo_salida.write("-----\n")
else:
    print("PRELOADED_STATE not found in the HTML.")

############ HOME MATCHES ID'S --> go to matches and get title and MAIN BET --> bets with MAINBET GET OUTCOMES (3) --> OUTCOMES label --> odds to get odds.