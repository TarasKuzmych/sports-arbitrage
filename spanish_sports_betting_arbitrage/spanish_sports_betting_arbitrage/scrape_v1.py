from bs4 import BeautifulSoup
import unicodedata
import requests
import sqlite3
import json
import re
import os
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

# Constants for the script
DATABASE_PATH = ROOT_DIR / 'odds.db'
AMOUNT_TO_BET = 100  # Fixed betting amount
MIN_ODDS = 1
MAX_ODDS = 10000
MIN_BETS = 2
MAX_BETS = 16

# Shared utility functions
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('ASCII')


def clean_name(name):
    # Remove all text within parentheses including the parentheses
    name = re.sub(r'\(.*?\)', '', name)

    name = remove_accents(name)

    # List of prefixes and suffixes to remove
    to_remove = ['@ ', 'RB', 'Athletic de ', 'Athletic', 'HSG', 'Racing de', ' del Norte', 'Eivissa', 'MVV', 'JC', 'Basquet', 'Sub 22', 'SUB 22', 'sub 22', 'SUB-22', 'sub-22', 'u22', 'Sub-22', 'U22','Sub 23', 'SUB 23', 'sub 23', 'SUB-23', 'sub-23', 'u23', 'Sub-23', 'U23','Sub 18', 'SUB 18', 'sub 18', 'SUB-18', 'sub-18', 'u18', 'Sub-18', 'U18','Sub 20', 'SUB 20', 'sub 20', 'SUB-20', 'sub-20', 'u20', 'Sub-20', 'U20','Sub 21', 'SUB 21', 'sub 21', 'SUB-21', 'sub-21', 'u21', 'Sub-21', 'U21', 'CSD', 'Atl', 'Ind', 'S.A', 'SSD', 'Baloncesto', 'Hotspur', 'GF', 'BM', 'Zacatecoluca', 'LUK', 'Women', 'Atsmon Playgrounds', 'Rio', 'Basket', 'WKS', 'Cazoo', 'Vitoria Gasteiz', 'Femenino', 'NIS', 'OPAP Athens', 'AD', 'Cs', 'OK', 'KK', 'FC', 'CF', 'CD', 'EC', 'SE', 'MG', 'FK', 'KF', 'AC', 'BK', 'TC', 'NK', 'SD', 'RJ', 'MT', 'BA', 'GO', 'SP', 'CE', 'SC', 'SV', 'RC', 'GC', 'AS', 'SS', 'UD', 'SK', 'CA', 'SL', 'AFC', 'CSC', 'BSC', 'RSC', 'GFC', 'LFC', 'SFC', 'RFC', 'VfL', 'VfB', 'FSV', 'SVW', 'JFC', 'DFC', 'HFC', 'Utd', 'SV', 'RCD', 'FBC', 'PFC', 'TSV', 'EFC', 'CFC', 'BFC', 'JSC', 'OSC', 'RRC', 'CSC', 'GSC', 'HSC', 'MSC', 'SSC', 'VSC', 'WSC', 'ZSC', 'AZ', 'PSV', 'FCZ', 'FCS', 'FCT', 'RKC', 'NAC', 'VVV', 'PEC', 'FCM', 'US', 'AJA', 'AZ', 'RBC', 'TFC', 'WFC', 'IFK', 'GIF', 'BIF', 'AIF', 'MFF', 'AIK', 'DIF', 'HIF', 'ÖFK', 'ÖSK', 'ÖIS', 'GIF', 'AaB', 'BIF', 'FCK', 'OB', 'VB', 'AGF', 'RFC', 'JJK', 'HJK', 'HIFK', 'SJK', 'KTP', 'KPV', 'PS', 'KuPS', 'MYPA', 'VPS', 'FF', 'IF', 'IK', 'BKV', 'BSV', 'B1901', 'B1903', 'B1909', 'B1913', 'KB', 'AB', 'VB', 'LFC', 'BC', 'CB', 'Lfc']

    # Remove '@' symbol if it's at the start of the name
    name = re.sub(r'^@ ?', '', name)

    # Modify the name by removing prefixes and suffixes at the beginning or end
    for item in to_remove:
        # Regular expression for prefix or suffix as a separate word
        word_pattern = r'\b' + re.escape(item) + r'\b'
        name = re.sub(word_pattern, '', name, flags=re.IGNORECASE)

    # Trim and remove extra spaces
    name = ' '.join(name.split())
    return name


def scrape_aupabet():
    url = 'https://www.aupabet.es'

    cookies = {
    
    }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        archivo_resultados = ROOT_DIR / 'aupabet/aupabet.txt'
        with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
            top_apostado_block = soup.find("div", id="bloqueApuestasDestacadas")
            if top_apostado_block:
                for nombre in top_apostado_block.find_all("div", class_="infoEve"):
                    nombres = {}
                    partido_span = nombre.find("span", class_="partido")
                    if partido_span:
                        equipos = re.sub(r' vs\. ', ' - ', partido_span.get_text(strip=True))
                        equipos = re.sub(r'\(\+ \d+\)', '', equipos).strip()
                        # Apply clean_name function
                        nombres['teams'] = clean_name(equipos)

                    cuotas_ul = nombre.find_next("ul", class_=lambda x: x and x.startswith('it_'))
                    if cuotas_ul:
                        nombres['odds'] = []
                        counter = 1
                        for li in cuotas_ul.find_all("li"):
                            cuota = li.find("span", class_="coef").get_text(strip=True)
                            cuota = cuota.replace(',', '.')
                            nombres['odds'].append(f"{counter}: {cuota}")
                            counter += 1

                    archivo_salida.write(f"{nombres.get('teams', 'N/A')}\n")
                    for odd in nombres.get('odds', []):
                        archivo_salida.write(f"  {odd}\n")
                    archivo_salida.write("-----\n")

        with open(ROOT_DIR / 'aupabet/aupabet.html', 'w', encoding='utf-8') as file:
            file.write(response.text)

    else:
        print(f'Error while making the request. Response code: {response.status_code}')

def scrape_betfair():
    url = 'https://www.betfair.es/sport/'

    cookies = {
        
        }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        html_content = response.text
        with open(ROOT_DIR / 'betfair/betfair.html', 'w', encoding='utf-8') as file:
            file.write(html_content)

        # Parse the HTML content of the page
        soup = BeautifulSoup(html_content, 'html.parser')

        events = []

        # Loop through each event
        for event_info in soup.find_all("div", class_="event-information"):
            # Skip elements with 'ui-inplay' in their class attribute
            if 'ui-inplay' in event_info['class']:
                continue  # Skip this iteration and move to the next element

            event = {"teams": [], "odds": []}

            # Extract teams participating in the event
            event_name_info = event_info.find("div", class_="event-name-info")
            if event_name_info:
                teams = event_name_info.find_all("span", class_=["home-team-name", "away-team-name"])
                for team in teams:
                    cleaned_team_name = clean_name(team.get_text(strip=True))
                    event["teams"].append(cleaned_team_name)

            # Extract betting odds
            runner_list = event_info.find("ul", class_="runner-list-selections")
            if runner_list:
                odds = []
                for selection in runner_list.find_all("li", class_="selection"):
                    outcome = selection.find("span", class_="ui-runner-price")
                    if outcome:
                        odds.append(outcome.get_text(strip=True))
                
                event["odds"] = odds

            events.append(event)

        archivo_resultados = ROOT_DIR / 'betfair/betfair.txt'
        with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
            for e in events:
                archivo_salida.write(" - ".join(e["teams"]) + "\n")
                for i, odd in enumerate(e["odds"], start=1):
                    archivo_salida.write(f"  {i}: {odd}\n")
                archivo_salida.write("-" * 5 + "\n")

    else:
        print(f'Error while making the request. Response code: {response.status_code}')


def scrape_interwetten():
    url = 'https://www.interwetten.es'

    cookies = {
        
        }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        with open(ROOT_DIR / 'interwetten/interwetten.html', 'w', encoding='utf-8') as file:
            file.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        archivo_resultados = ROOT_DIR / 'interwetten/interwetten.txt'

    with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        processed_events = set()

        bloques = soup.find_all('script', type='application/ld+json')
        for bloque in bloques:
            bloque_data = json.loads(bloque.string)
            bloque_name = bloque_data.get('name', 'Unknown Bloque')

            if '&#x' in bloque_name:
                continue

            bloque_name_cleaned = clean_name(bloque_name)
            bloque_row = bloque.find_next('tr', class_='b')
            betting_offers = bloque_row.find_all('td', class_='BETTINGOFFER') if bloque_row else []

            if betting_offers:
                processed_events.add(bloque_name_cleaned)
                archivo_salida.write(f"{bloque_name_cleaned}\n")
                counter = 1
                for offer in betting_offers:
                    odds = offer.find('strong').text.strip().replace(',', '.')
                    archivo_salida.write(f"  {counter}: {odds}\n")
                    counter += 1
                archivo_salida.write("-----\n")

        # Also find all rows that potentially contain tennis events
        tennis_rows = soup.find_all('tr', class_=re.compile(r'group\d'))
        for tennis_row in tennis_rows:
            bloque_name = tennis_row.find('td', class_='name').get_text(strip=True)

            if '&#x' in bloque_name:
                continue

            if bloque_name not in processed_events:
                processed_events.add(bloque_name)
                bloque_name_cleaned = clean_name(bloque_name)
                archivo_salida.write(f"{bloque_name_cleaned}\n")

                if tennis_row:
                    # Find all betting odds
                    betting_offers = tennis_row.find_all('td', class_='BETTINGOFFER')

                    counter = 1
                    for offer in betting_offers:
                        # Extract the betting data
                        odds = offer.find('strong').text.strip().replace(',', '.')
                        archivo_salida.write(f"  {counter}: {odds}\n")
                        counter += 1
                else:
                    archivo_salida.write("  No betting odds found\n")

                archivo_salida.write("-----\n")

def scrape_kirolbet():
    url = 'https://apuestas.kirolbet.es/'

    cookies = {
        
        }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        html_content = response.text

        with open(ROOT_DIR / 'kirolbet/kirolbet.html', 'w', encoding='utf-8') as file:
            file.write(html_content)

        soup = BeautifulSoup(html_content, 'html.parser')

        archivo_resultados = ROOT_DIR / 'kirolbet/kirolbet.txt'

        with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
            top_apostado_block = soup.find("div", id="bloqueApuestasDestacadas")
            if top_apostado_block:
                for nombre in top_apostado_block.find_all("div", class_="infoEve"):
                    nombres = {}
                    partido_span = nombre.find("span", class_="partido")
                    if partido_span:
                        equipos = re.sub(r' vs\. ', ' - ', partido_span.get_text(strip=True))
                        equipos = re.sub(r'\(\+ \d+\)', '', equipos).strip()
                        # Apply clean_name function
                        nombres['teams'] = clean_name(equipos)

                    cuotas_ul = nombre.find_next("ul", class_=lambda x: x and x.startswith('it_'))
                    if cuotas_ul:
                        nombres['odds'] = []
                        counter = 1
                        for li in cuotas_ul.find_all("li"):
                            cuota = li.find("span", class_="coef").get_text(strip=True)
                            cuota = cuota.replace(',', '.')
                            nombres['odds'].append(f"{counter}: {cuota}")
                            counter += 1

                    archivo_salida.write(f"{nombres.get('teams', 'N/A')}\n")
                    for odd in nombres.get('odds', []):
                        archivo_salida.write(f"  {odd}\n")
                    archivo_salida.write("-----\n")
    else:
        print(f'Error while making the request. Response code: {response.status_code}')


def scrape_marca():
    url = 'https://deportes.marcaapuestas.es/es'

    # Define the necessary cookies
    cookies = {
        
        }
    
    # Make the HTTP request with cookies
    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        with open(ROOT_DIR / 'marca/marca.html', 'w', encoding='utf-8') as html_file:
            html_file.write(response.text)

        with open(ROOT_DIR / 'marca/marca.txt', 'w', encoding='utf-8') as archivo_salida:
            eventos = soup.find_all('tr', class_='mkt')
            for evento in eventos:
                if evento.find('span', class_='will-be-inplay-image is-inplay'):
                    continue  # Skip live events

                participantes = []
                cuotas_info = []
                sequence_number = 1

                nombre_enfrentamiento_element = evento.find(class_='event-name')
                if nombre_enfrentamiento_element:
                    nombre_enfrentamiento = nombre_enfrentamiento_element.find('a').text.strip()
                    nombre_enfrentamiento = clean_name(nombre_enfrentamiento)
                    archivo_salida.write(f"Event: {nombre_enfrentamiento}\n")

                cuotas = evento.find_all('td', class_='seln')
                for cuota in cuotas:
                # Check for 'X' first
                    draw_label_element = cuota.find('span', class_='seln-draw-label')
                    if draw_label_element and draw_label_element.text.strip() == 'X':
                        cuota_valor_element = cuota.find('span', class_='price dec')
                        if cuota_valor_element:
                            cuota_valor = cuota_valor_element.text.strip()
                            cuotas_info.append(f"  2: {cuota_valor}")
                    else:
                        nombre_evento_element = cuota.find('span', class_='seln-name')
                        if nombre_evento_element:
                            nombre_evento = nombre_evento_element.text.strip()
                            participantes.append(nombre_evento)  # Add participant for the title
                            
                            cuota_valor_element = cuota.find('span', class_='price dec')
                            if cuota_valor_element:
                                cuota_valor = cuota_valor_element.text.strip()
                                cuotas_info.append(f"  {sequence_number}: {cuota_valor}")
                                sequence_number += 2 if sequence_number == 1 else 1  # Increment sequence number

                if participantes:
                    title = " - ".join([clean_name(p) for p in participantes])
                    archivo_salida.write(f"{title}\n")

                for cuota in cuotas_info:
                    archivo_salida.write(f"{cuota}\n")

                archivo_salida.write("-----\n")

    else:
        print(f'Error while making the request. Response code: {response.status_code}')   


def scrape_marathonbet():
    def is_nba(event_path):
        return 'Basketball/NBA' in event_path

    def is_nhl(event_path):
        return 'Ice+Hockey/NHL' in event_path

    url = 'https://www.marathonbet.es/es/?cppcids=all'

    # Define the necessary cookies
    cookies = {
        
        }

    # Make the HTTP request with cookies
    response = requests.get(url, cookies=cookies)

    # Check if the request was successful
    if response.status_code == 200:
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        with open(ROOT_DIR / 'marathonbet\marathonbet.html', 'w', encoding='utf-8') as file:
            file.write(response.text)

        archivo_resultados = ROOT_DIR / 'marathonbet/marathonbet.txt'
        with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
            nombres = soup.find_all('div', class_='bg coupon-row')

            for nombre in nombres:
                event_path = nombre.get('data-event-path', '')
                is_nba_event = is_nba(event_path)
                is_nhl_event = is_nhl(event_path)

                nombre_name = nombre['data-event-name'].replace(' vs ', ' - ').replace(' @ ', ' - ')
                nombre_name = clean_name(nombre_name)

                cuotas = {}
                cuota_elements = nombre.find_all('td', class_='price')

                for i, cuota in enumerate(cuota_elements, start=1):
                    cuota_value = cuota.find('span', class_='selection-link').get_text()
                    cuotas[str(i)] = cuota_value

                # Swap the teams for NBA or NHL events
                if is_nba_event or is_nhl_event:
                    nombre_name_parts = nombre_name.split(' - ')
                    if len(nombre_name_parts) == 2:
                        nombre_name = ' - '.join(nombre_name_parts[::-1])

                # Swap odds for NBA events and NHL events (1 and 3 for NHL)
                if is_nba_event:
                    cuotas['1'], cuotas['2'] = cuotas['2'], cuotas['1']
                elif is_nhl_event:
                    cuotas['1'], cuotas['3'] = cuotas['3'], cuotas['1']

                archivo_salida.write(f"{nombre_name}\n")
                for key, value in cuotas.items():
                    archivo_salida.write(f"  {key}: {value}\n")
                archivo_salida.write("-----\n")
    else:
        print(f'Error when making the request. Response code: {response.status_code}')


def scrape_pokerstars():
    url = 'https://www.pokerstars.es/sports/'
    cookies = {
        
        }

    # Define the regex patterns 
    patterns = {
        'next_races': re.compile(
            r"window\.__INITIAL_STATE__\['isp-sports-widget-next-races/62c1625f'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-next-races/62c1625f'\] \|\| {},\s*(\{.*?\})\);",
            re.DOTALL
        ),
        'in_play': re.compile(
            r"window\.__INITIAL_STATE__\['isp-sports-widget-home-in-play'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-home-in-play'\] \|\| {},\s*(\{.*?\})\);",
            re.DOTALL
        ),
        'upcoming_events': re.compile(
            r"window\.__INITIAL_STATE__\['isp-sports-widget-upcoming-events'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-upcoming-events'\] \|\| {},\s*(\{.*?\})\);",
            re.DOTALL
        ),
        'cms_banner' : re.compile(
            r"window\.__INITIAL_STATE__\['isp-sports-widget-cms-banner/d4f36c63'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-cms-banner/d4f36c63'\],\s*(\{.*?\})\);",
            re.DOTALL
        )
    }

    # Function to process data
    def process_data(pattern, html_content, archivo_salida, section):
        matches = pattern.search(html_content)
        if matches:
            json_string = matches.group(1)
            json_string = json_string.replace('u002F', '/') # erased .replace("'", '"') which may be needed as sometimes devs push updates. If starts playing definitely add the .replace
            try:
                data = json.loads(json_string)
                if section in ['in_play', 'upcoming_events']:
                    events_data = data.get('events', {})
                    markets_data = data.get('markets', {})
                    for event_id, event_info in events_data.items():
                        # Replace ' @ ' with ' - ' and clean the name
                        event_name = event_info.get("eventName", "Unknown Event").replace(' @ ', ' - ').replace(' v ', ' - ')
                        event_name = clean_name(event_name)

                        market_info = None
                        event_id_int = int(event_id) if event_id.isdigit() else None

                        for market_id, inner_dict in markets_data.items():
                            if isinstance(inner_dict, dict) and inner_dict.get('eventId') == event_id_int:
                                market_info = inner_dict
                                break

                        archivo_salida.write(f"{event_name}\n")
                        if market_info:
                            runners = market_info.get("runners", [])
                            for idx, runner in enumerate(runners, 1):
                                name = runner.get("runnerName", "Unknown")
                                odds = runner.get("winRunnerOdds", {}).get("decimalDisplayOdds", {}).get("decimalOdds", "N/A")
                                archivo_salida.write(f"  {idx}: {odds}\n")
                        else:
                            archivo_salida.write("  No odds available\n")
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
    archivo_resultados = ROOT_DIR / 'pokerstars/pokerstars.txt'

    response = requests.get(url, cookies=cookies)

    # Check for a successful request
    if response.status_code == 200:
        html_content = response.text

        # Save the HTML content for future checks
        with open(ROOT_DIR / 'pokerstars/pokerstars.html', 'w', encoding='utf-8') as file:
            file.write(html_content)
        
        # Open the output file to write results
        with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
            process_data(patterns['upcoming_events'], html_content, archivo_salida, 'upcoming_events')
            process_data(patterns['next_races'], html_content, archivo_salida, 'next_races')
            process_data(patterns['in_play'], html_content, archivo_salida, 'in_play')
    else:
        print(f'Error while making the request. Response code: {response.status_code}')


def scrape_winamax():
    url = 'https://www.winamax.es/apuestas-deportivas'

    cookies = {
        
        }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:

        with open(ROOT_DIR / 'winamax/winamax.html', 'w', encoding='utf-8') as html_file:
            html_file.write(response.text)

        soup = BeautifulSoup(response.text, 'html.parser')

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
            
            match_ids = matches_data.keys()  # Assuming the match IDs are the keys of the 'matches' dictionary
            
            with open(ROOT_DIR / 'winamax/winamax.txt', 'w', encoding='utf-8') as archivo_salida:
                for match_id, match_info in matches_data.items():
                    # Check if the match status is 'PREMATCH'
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
    else:
        print(f'Error while making the request. Response code: {response.status_code}')


def scrape_zebet():
    url = 'https://www.zebet.es'

    cookies = {
        
        }

    # Make the HTTP request with cookies
    response = requests.get(url, cookies=cookies)

    # Check if the request was successful (response code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save the HTML in a file for future checks
        with open(ROOT_DIR / 'zebet/zebet.html', 'w', encoding='utf-8') as file:
            file.write(response.text)
        
        # Process the content
        archivo_resultados = ROOT_DIR / 'zebet/zebet.txt'
        with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
            bloques = soup.find_all(class_=re.compile(r'item-bloc-type-\d+'))

            for bloque in bloques:
                nombre_enfrentamiento_element = bloque.find(class_='bet-event')
                
                if nombre_enfrentamiento_element:
                    nombre_enfrentamiento = nombre_enfrentamiento_element.find('a').text.strip()
                    nombre_enfrentamiento = clean_name(nombre_enfrentamiento)
                    nombre_enfrentamiento = nombre_enfrentamiento.replace(' / ', ' - ')  # Replace slashes with hyphens
                    archivo_salida.write(f"{nombre_enfrentamiento}\n")
                else:
                    archivo_salida.write("Nombre del enfrentamiento no encontrado\n")

                resultados = bloque.find_all(class_=re.compile(r"^bet-actor(?!odd)\d*"))

                if resultados:
                    contador_resultados = 1
                    for resultado in resultados:
                        odd = resultado.find('span', class_='pmq-cote')
                        if odd:
                            odd = odd.text.strip().replace(',', '.')  # Normalizar los valores de cuotas
                            archivo_salida.write(f"  {contador_resultados}: {odd}\n")
                            contador_resultados += 1
                else:
                    archivo_salida.write("Información de resultado no encontrada\n")

                archivo_salida.write("-----\n")

    else:
        print(f'Error making the request. Response code: {response.status_code}')
        

# Function to get or create an event match and return its ID
def get_or_create_event_match(cursor, event_name):
    try:
        # Check if the event match already exists
        cursor.execute("SELECT EventMatchID FROM EventMatches WHERE UniversalEventName = ?", (event_name,))
        match = cursor.fetchone()
        if match:
            return match[0]  # Return the existing EventMatchID
        else:
            # If not, create a new event match record
            cursor.execute("INSERT INTO EventMatches (UniversalEventName) VALUES (?)", (event_name,))
            return cursor.lastrowid  # Return the new EventMatchID
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return None

# Insert event record and return its ID
def get_or_create_event(cursor, event_name, bookie_name):
    event_match_id = get_or_create_event_match(cursor, event_name)
    try:
        # Check if the event already exists with the same EventMatchID
        cursor.execute("SELECT EventID FROM Events WHERE EventName = ? AND EventMatchID = ?", (event_name, event_match_id))
        event = cursor.fetchone()
        if event:
            return event[0]  # Return the existing EventID
        else:
            # If not, create a new event record
            cursor.execute("INSERT INTO Events (EventName, EventMatchID) VALUES (?, ?)", (event_name, event_match_id))
            return cursor.lastrowid  # Return the new EventID
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return None

# Insert outcomes and odds
def insert_outcomes_and_odds(cursor, event_id, outcomes, bookie_name):
    try:
        for outcome_desc, odds in outcomes:
            cursor.execute("INSERT INTO Outcomes (EventID, OutcomeDescription) VALUES (?, ?)", (event_id, outcome_desc))
            outcome_id = cursor.lastrowid
            cursor.execute("INSERT INTO Odds (OutcomeID, BookieName, OfferedOdds) VALUES (?, ?, ?)", (outcome_id, bookie_name, odds))
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")

# Function to process each bookie file
def process_bookie_file(filepath, cursor):
    bookie_name = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, 'r', encoding='utf-8') as file:
        event_blocks = file.read().strip().split('-----')
        for block in event_blocks:
            parts = block.strip().split('\n')
            if parts:
                event_name = parts[0].strip()
                event_id = get_or_create_event(cursor, event_name, bookie_name)
                if event_id is not None:
                    outcomes = []
                    for line in parts[1:]:
                        try:
                            outcome_num, odd = line.split(':')
                            outcome_desc = f"Outcome {outcome_num.strip()}"
                            odd = float(odd.strip())
                            outcomes.append((outcome_desc, odd))
                        except ValueError as e:
                            print(f"Error parsing line '{line}': {e}")
                            continue
                    insert_outcomes_and_odds(cursor, event_id, outcomes, bookie_name)


def clear_existing_data(cursor):
    try:
        cursor.execute("DELETE FROM Odds")
        cursor.execute("DELETE FROM Outcomes")
        cursor.execute("DELETE FROM Events")
        cursor.execute("DELETE FROM EventMatches")
    except sqlite3.DatabaseError as e:
        print(f"Database error while clearing data: {e}")


# Main function to walk through the directories and process files
def process_directories(root_dir):
    with sqlite3.connect(ROOT_DIR / 'odds.db') as conn:
        cursor = conn.cursor()
        clear_existing_data(cursor)  # Clear existing data before processing new files
        for subdir, dirs, files in os.walk(root_dir):
            folder_name = os.path.basename(subdir)
            for filename in files:
                if filename.endswith('.txt') and os.path.splitext(filename)[0] == folder_name:
                    filepath = os.path.join(subdir, filename)
                    try:
                        process_bookie_file(filepath, cursor)
                    except Exception as e:
                        print(f"An error occurred while processing file {filepath}: {e}")
        conn.commit()

def get_max_odds_from_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        E.EventName,
        O.OutcomeDescription,
        MAX(OD.OfferedOdds) AS MaxOfferedOdds,
        (SELECT GROUP_CONCAT(OD2.BookieName) 
         FROM Odds OD2 
         WHERE OD2.OutcomeID = O.OutcomeID AND OD2.OfferedOdds = MAX(OD.OfferedOdds)) AS BookiesWithMaxOdds
    FROM 
        Events E
    JOIN 
        Outcomes O ON E.EventID = O.EventID
    JOIN 
        Odds OD ON O.OutcomeID = OD.OutcomeID
    GROUP BY 
        E.EventName, 
        O.OutcomeDescription
    """)

    results = cursor.fetchall()
    conn.close()

    max_odds_dict = {}
    for event_name, outcome_description, max_odds, bookies_with_max_odds in results:
        if event_name not in max_odds_dict:
            max_odds_dict[event_name] = {}
        max_odds_dict[event_name][outcome_description] = (max_odds, bookies_with_max_odds)
    return max_odds_dict

# Function to write the max odds to a file in the desired format
def write_max_odds_to_file(max_odds_dict, file_path):
    with open(file_path, 'w') as file:
        for event_name, outcomes in max_odds_dict.items():
            file.write("-------------------------\n")
            file.write(f"'{event_name}':\n")
            for outcome_desc, (max_odds, bookies) in outcomes.items():
                file.write(f"{outcome_desc}: {max_odds} Bookie(s): {bookies}\n")
            file.write("-------------------------\n")

# Function to calculate stakes for the equal pay strategy
def calculate_stakes_equal_pay(odds, probability, amount_to_bet):
    return [(probability / odd) * amount_to_bet for odd in odds]

# Function to calculate stakes for the max risk strategy
def calculate_stakes_max_risk(inverse_odds, odds, amount_to_bet):
    max_odd_index = inverse_odds.index(min(inverse_odds))
    sum_of_other_stakes = sum(inverse_odd * amount_to_bet for i, inverse_odd in enumerate(inverse_odds) if i != max_odd_index)
    
    stakes = [inverse_odd * amount_to_bet if i != max_odd_index else amount_to_bet - sum_of_other_stakes for i, inverse_odd in enumerate(inverse_odds)]
    return stakes

def write_strategy_to_file(file, stakes, total_profit, strategy_title):
    file.write(strategy_title + "\n")
    for i, stake in enumerate(stakes):
        file.write(f"Stake for bet {i+1}: {stake:,.2f}$\n")
    file.write(f"Total profit: {total_profit:,.2f}$\n")
    file.write("-------------------------\n")

# Function to calculate the arbitrage probability
def arb_calculator(odds):
    odds_probability = sum(1/odd for odd in odds)
    return 1 / odds_probability if odds_probability < 1 else "Not arbitrageable"

if __name__ == "__main__":
    scrape_aupabet()
    scrape_betfair()
    scrape_interwetten()
    scrape_kirolbet()
    scrape_marca()
    scrape_marathonbet()
    scrape_pokerstars()
    scrape_winamax()
    scrape_zebet()

    # Call the main function with the path to your top root directory
    process_directories(ROOT_DIR)

    max_odds_dict = get_max_odds_from_db()

    # Write the max odds to maxodds.txt
    write_max_odds_to_file(max_odds_dict, ROOT_DIR / 'maxodds.txt')

    with open(ROOT_DIR / 'arbitrageable.txt', 'w') as file:
        for event_name, outcomes in max_odds_dict.items():
            odds = [info[0] for info in outcomes.values()]
            bookies = [info[1] for info in outcomes.values()]
            probability = arb_calculator(odds)

            if probability != "Not arbitrageable":
                file.write("-------------------------\n")
                file.write(f"'{event_name}':\n")
                for outcome_desc, (max_odds, bookie) in outcomes.items():
                    file.write(f"{outcome_desc}: {max_odds} Bookie(s): {bookie}\n")
                file.write("-------------------------\n")
                
                stakes_equal_pay = calculate_stakes_equal_pay(odds, probability, AMOUNT_TO_BET)
                total_profit_equal_pay = (probability - 1) * AMOUNT_TO_BET
                write_strategy_to_file(file, stakes_equal_pay, total_profit_equal_pay, "For equal pay strategy:")

                inverse_odds = [1/odd for odd in odds]
                stakes_max_risk = calculate_stakes_max_risk(inverse_odds, odds, AMOUNT_TO_BET)
                total_profit_max_risk = sum((stake * odd) - AMOUNT_TO_BET for stake, odd in zip(stakes_max_risk, odds))
                write_strategy_to_file(file, stakes_max_risk, total_profit_max_risk, "For max risk strategy:")
                file.write("\n")
                