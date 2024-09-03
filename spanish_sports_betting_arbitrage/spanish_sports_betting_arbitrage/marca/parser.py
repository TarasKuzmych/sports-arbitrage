from bs4 import BeautifulSoup
import unicodedata
import re
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

# Shared utility functions
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('ASCII')

women_categories = {
    'Women': 'Femenino', 'women': 'Femenino', 'Femenino': 'Femenino', ' (W) ': 'Femenino', 'Ladies': 'Femenino'
}
age_categories = {
    'Sub 18': 'U18', 'SUB 18': 'U18', 'sub 18': 'U18', 'SUB-18': 'U18', 'sub-18': 'U18', 'u18': 'U18', 'Sub-18': 'U18',
    'Sub 20': 'U20', 'SUB 20': 'U20', 'sub 20': 'U20', 'SUB-20': 'U20', 'sub-20': 'U20', 'u20': 'U20', 'Sub-20': 'U20', 
    'Sub 21': 'U21', 'SUB 21': 'U21', 'sub 21': 'U21', 'SUB-21': 'U21', 'sub-21': 'U21', 'u21': 'U21', 'Sub-21': 'U21',
    'Sub 22': 'U22', 'SUB 22': 'U22', 'sub 22': 'U22', 'SUB-22': 'U22', 'sub-22': 'U22', 'u22': 'U22', 'Sub-22': 'U22',
    'Sub 23': 'U23', 'SUB 23': 'U23', 'sub 23': 'U23', 'SUB-23': 'U23', 'sub-23': 'U23', 'u23': 'U23', 'Sub-23': 'U23',
    'Sub 25': 'U25', 'SUB 25': 'U25', 'sub 25': 'U25', 'SUB-25': 'U25', 'sub-25': 'U25', 'u25': 'U25', 'Sub-25': 'U25'
}

def standardize_categories(event_name, category_mapping):
    # First handle the '(W)' case specifically
    event_name = re.sub(r'\(W\)', 'Femenino', event_name, flags=re.IGNORECASE)
    
    # Split the event name into parts to handle each team separately
    parts = event_name.split(' - ')
    standardized_parts = []

    for part in parts:
        # Check and replace each variation with the standard term
        for variation, standard in category_mapping.items():
            # Skip the specific case that has already been handled
            if variation == '(W)':
                continue
            
            # Replace the variation with the standard term if it's not already there
            if standard not in part:
                part = re.sub(r'\b' + re.escape(variation) + r'\b', standard, part, flags=re.IGNORECASE)
        
        # Clean up any repeated standard terms and trim whitespace
        part = re.sub(r'\b' + re.escape(standard) + r'\b', standard, part)  # Apply the standard term
        part = ' '.join(part.split())  # Remove extra spaces
        standardized_parts.append(part)

    # Rejoin the standardized parts
    return ' - '.join(standardized_parts)

def clean_name(name):
    name = remove_accents(name)

    # Extract age category if present
    age_category = None
    for category in age_categories.values():
        if category in name:
            age_category = category
            break

    name = standardize_categories(name, age_categories)
    name = standardize_categories(name, women_categories)

    # Remove all occurrences of age categories
    for category in age_categories.values():
        name = re.sub(rf'\b{category}\b', '', name)

    name = re.sub(r'\((?!W\))[^)]*\)', '', name)

    # Complete list of prefixes and suffixes to remove
    to_remove = ['@ ', 'RB', 'HSG', 'MVV', 'JC', 'Basquet', 'CSD', 'Atl', 'Ind', 'S.A', 'SSD', 'Baloncesto', 'GF', 'BM', 'LUK', 'Rio', 'Basket', 'WKS', 'Cazoo',  'NIS', 'AD', 'Cs', 'OK', 'KK', 'FC', 'CF', 'CD', 'EC', 'SE', 'MG', 'FK', 'KF', 'AC', 'BK', 'TC', 'NK', 'SD', 'RJ', 'MT', 'BA', 'GO', 'SP', 'CE', 'SC', 'SV', 'RC', 'GC', 'AS', 'SS', 'UD', 'SK', 'CA', 'SL', 'AFC', 'CSC', 'BSC', 'RSC', 'GFC', 'LFC', 'SFC', 'RFC', 'VfL', 'VfB', 'FSV', 'SVW', 'JFC', 'DFC', 'HFC', 'Utd', 'SV', 'RCD', 'FBC', 'PFC', 'TSV', 'EFC', 'CFC', 'BFC', 'JSC', 'OSC', 'RRC', 'CSC', 'GSC', 'HSC', 'MSC', 'SSC', 'VSC', 'WSC', 'ZSC', 'AZ', 'PSV', 'FCZ', 'FCS', 'FCT', 'RKC', 'NAC', 'VVV', 'PEC', 'FCM', 'US', 'AJA', 'AZ', 'RBC', 'TFC', 'WFC', 'IFK', 'GIF', 'BIF', 'AIF', 'MFF', 'AIK', 'DIF', 'HIF', 'ÖFK', 'ÖSK', 'ÖIS', 'GIF', 'AaB', 'BIF', 'FCK', 'OB', 'VB', 'AGF', 'RFC', 'JJK', 'HJK', 'HIFK', 'SJK', 'KTP', 'KPV', 'PS', 'KuPS', 'MYPA', 'VPS', 'FF', 'IF', 'IK', 'BKV', 'BSV', 'B1901', 'B1903', 'B1909', 'B1913', 'KB', 'AB', 'VB', 'LFC', 'BC', 'CB', 'Lfc']

    # Remove '@' symbol if it's at the start of the name
    name = re.sub(r'^@ ?', '', name)

    # Modify the name by removing prefixes and suffixes at the beginning or end
    for item in to_remove:
        word_pattern = r'\b' + re.escape(item) + r'\b'
        name = re.sub(word_pattern, '', name, flags=re.IGNORECASE)

    # Reapply the extracted age category uniformly to both teams
    if age_category:
        name = re.sub(r'(^.*?)( - )', rf'\1 {age_category}\2', name)
        team1, separator, team2 = name.partition(' - ')
        if age_category not in team2:
            team2 = f'{team2} {age_category}'
        name = f'{team1}{separator}{team2}'

    # Trim and remove extra spaces
    name = ' '.join(name.split())
    return name

ruta_archivo = ROOT_DIR / 'marca/marca.html'
archivo_resultados = ROOT_DIR / 'marca/marca.txt'

# Create a set to store processed event names
seen_titles = set()

with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
    html_content = archivo.read()

soup = BeautifulSoup(html_content, 'html.parser')

base_url = "https://deportes.marcaapuestas.es"

with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
    eventos = soup.find_all('tr', class_='mkt')
    for evento in eventos:
        # Check if the event is live
        if evento.find('span', class_='will-be-inplay-image is-inplay'):
            continue  # Skip this event as it's a live event

        participantes = []
        cuotas_info = []
        sequence_number = 1

        cuotas = evento.find_all('td', class_='seln')
        for cuota in cuotas:
            draw_label_element = cuota.find('span', class_='seln-draw-label')
            if draw_label_element and draw_label_element.text.strip() == 'X':
                cuota_valor_element = cuota.find('span', class_='price dec')
                if cuota_valor_element:
                    cuota_valor = cuota_valor_element.text.strip()
                    cuotas_info.append(f"  {sequence_number}: {cuota_valor}")
            else:
                nombre_evento_element = cuota.find('span', class_='seln-name')
                if nombre_evento_element:
                    nombre_evento = nombre_evento_element.text.strip()
                    participantes.append(nombre_evento)

                    cuota_valor_element = cuota.find('span', class_='price dec')
                    if cuota_valor_element:
                        cuota_valor = cuota_valor_element.text.strip()
                        cuotas_info.append(f"  {sequence_number}: {cuota_valor}")

            sequence_number += 1

        if participantes:
            title = " - ".join(participantes)
            if title not in seen_titles:
                seen_titles.add(title)

                # Attempt to find the event link
                event_link_element = evento.find('a', href=True)
                event_link = base_url + event_link_element['href'] if event_link_element else "Link not found"

                clean_title = clean_name(title)
                archivo_salida.write(f"{clean_title}\n")
                for cuota in cuotas_info:
                    archivo_salida.write(f"{cuota}\n")
                archivo_salida.write(f"link -> {event_link}\n")
                archivo_salida.write("-----\n")

    eventos = soup.find_all('tbody', class_='')
    for evento in eventos:
        rows = evento.find_all('tr')
        if len(rows) < 2:  # Ensure there are at least two rows for teams
            continue

        event_name_cell = rows[0].find('td', class_='event-name')
        if event_name_cell:
            anchor = event_name_cell.find('a')
            if anchor and 'href' in anchor.attrs:
                href = anchor['href']
                # Construct the full event link
                event_link = base_url + href

                # Splitting the href to extract team names
                team_names = re.search(r'/([^/]+)-%40-([^/]+)$', href)
                if team_names:
                    team1, team2 = team_names.groups()
                    team1 = team1.replace('-', ' ')
                    team2 = team2.replace('-', ' ')

                    # Fetching odds
                    cuotas_info = []
                    for i, row in enumerate(rows[:2]):
                        cuota_element = row.find('td', class_='mkt-sort mkt-sort-H2HT')
                        if cuota_element:
                            cuota_valor_element = cuota_element.find('span', class_='price dec')
                            if cuota_valor_element:
                                cuota_valor = cuota_valor_element.text.strip()
                                cuotas_info.append(f"  {i + 1}: {cuota_valor}")

                    # Only write to file if both teams have odds
                    if len(cuotas_info) == 2:
                        event_name = f"{team1} - {team2}"
                        archivo_salida.write(f"{event_name}\n")
                        for cuota in cuotas_info:
                            archivo_salida.write(f"{cuota}\n")
                        archivo_salida.write(f"link -> {event_link}\n")
                        archivo_salida.write("-----\n")
                        