from multiprocessing import Pool, cpu_count
from bs4 import BeautifulSoup, Tag
import unicodedata
import time
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
    to_remove = [' 1892', ' 05', '1846', '1.', 'UVC', 'UNI', 'Spar Citylift', 'Fredrikstad', 'Hockey', 'GTK','GS', 'Handbold', 'Saint-Germain', 'SSS', 'LPC', 'LOSC', 'Jestravi', 'LHK', 'Deportivo', 'SAD', 'HC', 'UD', 'UE', 'SSV', 'de Vigo', 'MKS', 'CSM', 'KS', 'HK', 'Atletic', 'Balompie', '@ ', 'RB', 'Athletic de ', 'HSG', 'Racing de', ' del Norte', 'Eivissa', 'MVV', 'JC', 'Basquet', 'CSD', 'Atl', 'Ind', 'S.A', 'SSD', 'Baloncesto', 'Hotspur', 'GF', 'BM', 'Zacatecoluca', 'LUK', 'Atsmon Playgrounds', 'Rio', 'Basket', 'WKS', 'Cazoo', 'Vitoria Gasteiz', 'NIS', 'OPAP Athens', 'AD', 'Cs', 'OK', 'KK', 'FC', 'CF', 'CD', 'EC', 'SE', 'MG', 'FK', 'KF', 'AC', 'BK', 'TC', 'NK', 'SD', 'RJ', 'MT', 'BA', 'GO', 'SP', 'CE', 'SC', 'SV', 'RC', 'GC', 'AS', 'SS', 'UD', 'SK', 'CA', 'SL', 'AFC', 'CSC', 'BSC', 'RSC', 'GFC', 'LFC', 'SFC', 'RFC', 'VfL', 'VfB', 'FSV', 'SVW', 'JFC', 'DFC', 'HFC', 'Utd', 'SV', 'RCD', 'FBC', 'PFC', 'TSV', 'EFC', 'CFC', 'BFC', 'JSC', 'OSC', 'RRC', 'CSC', 'GSC', 'HSC', 'MSC', 'SSC', 'VSC', 'WSC', 'ZSC', 'AZ', 'PSV', 'FCZ', 'FCS', 'FCT', 'RKC', 'NAC', 'VVV', 'PEC', 'FCM', 'US', 'AJA', 'AZ', 'RBC', 'TFC', 'WFC', 'IFK', 'GIF', 'BIF', 'AIF', 'MFF', 'AIK', 'DIF', 'HIF', 'ÖFK', 'ÖSK', 'ÖIS', 'GIF', 'AaB', 'BIF', 'FCK', 'OB', 'VB', 'AGF', 'RFC', 'JJK', 'HJK', 'HIFK', 'SJK', 'KTP', 'KPV', 'PS', 'KuPS', 'MYPA', 'VPS', 'FF', 'IF', 'IK', 'BKV', 'BSV', 'B1901', 'B1903', 'B1909', 'B1913', 'KB', 'AB', 'VB', 'LFC', 'BC', 'CB', 'Lfc']

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

start_time = time.time()

ruta_archivo = ROOT_DIR / 'bwin/bwin.html'
archivo_resultados = ROOT_DIR / 'bwin/bwin.txt'

# Create a dict to store processed event names
processed_events = {}

with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
    html_content = archivo.read()

soup = BeautifulSoup(html_content, 'html5lib')

base_url = 'https://sports.bwin.es'

with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
    # Variables to keep track of the current header and its relevant keywords
    current_header = None
    relevant_headers = ['money line', '2 way', 'resultado 1x2']

    # Iterate through all elements in the document in order
    for element in soup.find_all():
        if 'grid-group' in element.get('class', []):
            # Check if the element is a header with relevant keywords
            header_text = element.get_text().lower()
            if any(keyword in header_text for keyword in relevant_headers):
                current_header = header_text
                print(f"Found header: {current_header.strip()}")
        elif 'grid-event' in element.get('class', []):
            # If the element is an event block and we have a relevant header
            if current_header and any(keyword in current_header for keyword in relevant_headers):
                # Extract participant names to form the event title
                participant_elements = element.find_all(class_="participant")
                participants = [participant.get_text().strip() for participant in participant_elements]
                event_name = ' - '.join(participants)

                # Clean the event title
                title = event_name if event_name else None

                # Debug: Print event name
                print(f"Processing event: {title}")

                # Skip processing if no title or if the event name already exists in processed_events
                if not title or title in processed_events:
                    print("Skipping event due to missing title or already processed")
                    continue

                # Initialize relevant_groups list
                relevant_groups = []

                # Find all option groups within the event block
                option_groups = element.find_all('ms-option-group', class_="grid-option-group")
                
                # Collect odds only if they are under 'Money Line', '2 Way', or 'Resultado 1X2'
                all_odds = []
                for option_group in option_groups:
                    group_text = option_group.get_text().lower()
                    if any(keyword in group_text for keyword in relevant_headers):
                        odds_elements = option_group.find_all(class_="option-value")
                        odds = [odds_element.get_text().strip() for odds_element in odds_elements]
                        all_odds.extend(odds)

                # Debug: Print extracted odds
                print(f"Extracted odds for event {title}: {all_odds}")

                # Find the link of the event
                link_element = element.find('a', class_="grid-info-wrapper fixed")
                event_link = base_url + link_element.get('href') if link_element else None

                # Skip the event if there are no odds
                if len(all_odds) > 0:
                    processed_events[title] = {
                        'event_block': element,
                        'odds': all_odds,
                        'link': event_link  # Store the link in the processed_events dict
                    }

    # Write the processed events to file
    for title, event_info in processed_events.items():
        if title and event_info['odds']:
            archivo_salida.write(f"{title}\n")
            for i, odd in enumerate(event_info['odds'], start=1):
                archivo_salida.write(f"  {i}: {odd}\n")
            if event_info['link']:  # Check if the link is available and write it to the file
                archivo_salida.write(f"link -> {event_info['link']}\n")
            archivo_salida.write(f"-----\n")

# Output the final result for debugging purposes
print(f"Processed {len(processed_events)} events")

end_time = time.time()
elapsed_time = end_time - start_time
minutes = (elapsed_time / 60)
print(f"Script executed in {elapsed_time:.2f} seconds.")
print(f"Script executed in {minutes:.2f} minutes.")
