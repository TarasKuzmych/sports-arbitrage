import json
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


# Function to process and write data
def process_data(pattern, html_content, archivo_salida, section):
    matches = pattern.finditer(html_content) # if not working change finditer to findall
    for match in matches:  # Iterate over each match object
        json_string = match.group(1)
        json_string = json_string.replace('u002F', '/') # erased .replace("'", '"') which may be needed as sometimes devs push updates. If starts playing definitely add the .replace
        try:
            data = json.loads(json_string)
            if section in ['in_play', 'upcoming_events', 'competition_events', 'cms_banner']:
                competitions_data = data.get('competitions', {})
                event_types_data = data.get('eventTypes', {})
                events_data = data.get('events', {})
                markets_data = data.get('markets', {})
                for event_id, event_info in events_data.items():
                    # Check if event is not in play
                    if not event_info.get("isInPlay", False):  # This line filters out events that are in play 
                        # Replace ' @ ' with ' - ' and clean the name
                        event_name = event_info.get("eventName", "Unknown Event").replace(' @ ', ' - ').replace(' v ', ' - ')
                        event_name = clean_name(event_name)

                        market_info = None
                        event_id_int = int(event_id) if event_id.isdigit() else None

                        event_id_str = str(event_info.get('eventId'))
                        competition_id = str(event_info.get('competitionId'))
                        event_slug = event_info.get('eventSlug')
                        event_type_id = str(event_info.get('eventTypeId'))

                        # List of all markets for this event
                        event_markets = [inner_dict for market_id, inner_dict in markets_data.items()
                                        if isinstance(inner_dict, dict) and inner_dict.get('eventId') == event_id_int]

                        if len(event_markets) > 1:
                            # If multiple markets, filter for 'MONEY_LINE'
                            for market in event_markets:
                                if market.get('marketType') == 'MONEY_LINE':
                                    market_info = market
                                    break
                        elif event_markets:
                            # If only one market or no 'MONEY_LINE' market in multiple, use the available market
                            market_info = event_markets[0]

                        competition_slug = competitions_data.get(competition_id, {}).get('competitionSlug')
                        event_type_slug = event_types_data.get(event_type_id, {}).get('eventTypeSlug')

                        # Construct the event URL
                        if competition_slug and event_slug and event_type_slug:
                            base_url = "https://www.pokerstars.es/sports/"
                            event_url = f"{base_url}{event_type_slug}/{event_type_id}/{competition_slug}/{competition_id}/{event_slug}/{event_id_str}/"


                        archivo_salida.write(f"{event_name}\n")
                        if market_info:
                            runners = market_info.get("runners", [])
                            for idx, runner in enumerate(runners, 1):
                                name = runner.get("runnerName", "Unknown")
                                odds = runner.get("winRunnerOdds", {}).get("decimalDisplayOdds", {}).get("decimalOdds", "N/A")
                                archivo_salida.write(f"  {idx}: {odds}\n")
                            # Addition to write the event URL
                            archivo_salida.write(f"link -> {event_url}\n")
                        archivo_salida.write("-----\n")

            elif section == 'next_races':
                markets_data = data.get('markets', {})
                for market_id, market_info in markets_data.items():
                    runners_names = []
                    runners_odds = []
                    runners = market_info.get("runners", [])
                    incomplete_market = False

                    for idx, runner in enumerate(runners, 1):
                        name = runner.get("runnerName", "Unknown")
                        if "favorito sin nombre" not in name.lower():
                            odds = runner.get("winRunnerOdds", {}).get("decimalDisplayOdds", {}).get("decimalOdds", None)
                            if odds is None:
                                incomplete_market = True
                                break
                            runners_names.append(name)
                            runners_odds.append(f"  {idx}: {odds}")

                    if not incomplete_market and runners_names:
                        archivo_salida.write(' - '.join(runners_names) + "\n")
                        for runner_odds in runners_odds:
                            archivo_salida.write(runner_odds + "\n")
                        archivo_salida.write("-----\n")

        except json.JSONDecodeError as e:
            print(f"An error occurred while parsing JSON for {section}: {e}")
    else:
        print(f"No matching JSON found in the HTML file for {section}.")


# File paths
ruta_archivo = ROOT_DIR / 'pokerstars/pokerstars.html'
archivo_resultados = ROOT_DIR / 'pokerstars/pokerstars.txt'

with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
    html_content = archivo.read()

# Define regex patterns
patterns = {
    'next_races': re.compile(
        r"window\.__INITIAL_STATE__\['isp-sports-widget-next-races(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-next-races(?:/.+?)?'\] \|\| {},\s*(\{.*?\})\);",
        re.DOTALL
    ),
    'in_play': re.compile(
        r"window\.__INITIAL_STATE__\['isp-sports-widget-home-in-play(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-home-in-play(?:/.+?)?'\] \|\| {},\s*(\{.*?\})\);",
        re.DOTALL
    ),
    'upcoming_events': re.compile(
        r"window\.__INITIAL_STATE__\['isp-sports-widget-upcoming-events(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-upcoming-events(?:/.+?)?'\] \|\| {},\s*(\{.*?\})\);",
        re.DOTALL
    ),
    'cms_banner' : re.compile(
        r"window\.__INITIAL_STATE__\['isp-sports-widget-cms-banner(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-cms-banner(?:/.+?)?'\],\s*(\{.*?\})\);",
        re.DOTALL
    ),
    'competition_events': re.compile(
        r"window\.__INITIAL_STATE__\['isp-sports-widget-competition-events(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-competition-events(?:/.+?)?'\] \|\| {},\s*(\{.*?\})\);",
        re.DOTALL
    )
}
# Now process these patterns similarly as done for 'in_play' and 'upcoming_events'
with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
    #process_data(patterns['upcoming_events'], html_content, archivo_salida, 'upcoming_events')
    #process_data(patterns['next_races'], html_content, archivo_salida, 'next_races')
    #process_data(patterns['in_play'], html_content, archivo_salida, 'in_play')
    process_data(patterns['competition_events'], html_content, archivo_salida, 'competition_events')
    #process_data(patterns['cms_banner'], html_content, archivo_salida, 'cms_banner')