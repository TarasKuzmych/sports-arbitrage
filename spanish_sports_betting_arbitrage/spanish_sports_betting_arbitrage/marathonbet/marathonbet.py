import requests
from bs4 import BeautifulSoup
import unicodedata
import random
import time
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
    to_remove = ['CSD', 'Atl', 'Ind', 'S.A', 'SSD', 'Baloncesto', 'Hotspur', 'GF', 'BM', 'Zacatecoluca', 'LUK', 'Women', 'Atsmon Playgrounds', 'Rio', 'Basket', 'WKS', 'Cazoo', 'Vitoria Gasteiz', 'Femenino', 'NIS', 'OPAP Athens', 'AD', 'Cs', 'OK', 'KK', 'FC', 'CF', 'CD', 'EC', 'SE', 'MG', 'FK', 'KF', 'AC', 'BK', 'TC', 'NK', 'SD', 'RJ', 'MT', 'BA', 'GO', 'SP', 'CE', 'SC', 'SV', 'RC', 'GC', 'AS', 'SS', 'UD', 'SK', 'CA', 'SL', 'AFC', 'CSC', 'BSC', 'RSC', 'GFC', 'LFC', 'SFC', 'RFC', 'VfL', 'VfB', 'FSV', 'SVW', 'JFC', 'DFC', 'HFC', 'Utd', 'SV', 'RCD', 'FBC', 'PFC', 'TSV', 'EFC', 'CFC', 'BFC', 'JSC', 'OSC', 'RRC', 'CSC', 'GSC', 'HSC', 'MSC', 'SSC', 'VSC', 'WSC', 'ZSC', 'AZ', 'PSV', 'FCZ', 'FCS', 'FCT', 'RKC', 'NAC', 'VVV', 'PEC', 'FCM', 'US', 'AJA', 'AZ', 'RBC', 'TFC', 'WFC', 'IFK', 'GIF', 'BIF', 'AIF', 'MFF', 'AIK', 'DIF', 'HIF', 'ÖFK', 'ÖSK', 'ÖIS', 'GIF', 'AaB', 'BIF', 'FCK', 'OB', 'VB', 'AGF', 'RFC', 'JJK', 'HJK', 'HIFK', 'SJK', 'KTP', 'KPV', 'PS', 'KuPS', 'MYPA', 'VPS', 'FF', 'IF', 'IK', 'BKV', 'BSV', 'B1901', 'B1903', 'B1909', 'B1913', 'KB', 'AB', 'VB', 'LFC', 'BC', 'CB', 'Lfc']

    # Modify the name by removing prefixes and suffixes at the beginning or end
    for item in to_remove:
        # Regular expression for prefix or suffix as a separate word
        word_pattern = r'\b' + re.escape(item) + r'\b'
        name = re.sub(word_pattern, '', name, flags=re.IGNORECASE)

    # Trim and remove extra spaces
    name = ' '.join(name.split())
    return name


def scrape_marathonbet():
    def is_nba(event_path):
        return 'Basketball/NBA' in event_path

    def is_nhl(event_path):
        return 'Ice+Hockey/NHL' in event_path

    # Base URL for constructing the event link
    base_url = 'https://www.marathonbet.es/es/'

    url = 'https://www.marathonbet.es/es/?cppcids=all'
    cookies = {
    
    }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        with open(ROOT_DIR / 'marathonbet/marathonbet_links.html', 'w', encoding='utf-8') as file:
            file.write(response.text)
    else:
        print(f'Error al realizar la solicitud. Código de respuesta: {response.status_code}')

    # Read the HTML file and parse it
    with open(ROOT_DIR / 'marathonbet/marathonbet_links.html', 'r', encoding='utf-8') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')
    links = set()

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if (href.startswith('/es/betting/') and 
            'Outright' not in href and 
            'Specials' not in href and
            '+vs+' not in href and
            '+%40+' not in href):
            full_link = 'https://www.marathonbet.es' + href
            slash_count = full_link.count('/')
            if slash_count == 6:
                links.add(full_link)

    # Save the extracted links to a file
    with open(ROOT_DIR / 'marathonbet/marathonbet_links.txt', 'w', encoding='utf-8') as file:
        for link in links:
            file.write(link + '\n')

    # Open 'marathonbet.html' in write mode to reset its content
    with open(ROOT_DIR / 'marathonbet/marathonbet.html', 'w', encoding='utf-8') as file:
        pass  # Simply opening in 'w' mode will clear the file

    # Read the links from the 'marathonbet_links.txt' file
    with open(ROOT_DIR / 'marathonbet/marathonbet_links.txt', 'r', encoding='utf-8') as file:
        links = file.readlines()

    # Loop through each link
    for link in links:
        link = link.strip()  # Remove any leading/trailing whitespace or newline characters

        # Wait for a random time between 2.55 and 4.35 seconds
        time.sleep(random.uniform(2.55, 4.35))

        # Send a request to the link
        response = requests.get(link)

        # Check if the request was successful (response code 200)
        if response.status_code == 200:
            # Append the HTML content to 'marathonbet.html'
            with open(ROOT_DIR / 'marathonbet/marathonbet.html', 'a', encoding='utf-8') as file:
                file.write(response.text + '\n')
        else:
            print(f'Error making the request to {link}. Response code: {response.status_code}')

    ruta_archivo = ROOT_DIR / 'marathonbet/marathonbet.html'
    archivo_resultados = ROOT_DIR / 'marathonbet/marathonbet.txt'

    def is_nba(event_path):
        return 'Basketball/NBA' in event_path

    def is_nhl(event_path):
        return 'Ice+Hockey/NHL' in event_path

    # Set to track unique events
    unique_events = set()

    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        html_content = archivo.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Base URL for constructing the event link
    base_url = 'https://www.marathonbet.es/es/betting/'

    with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        nombres = soup.find_all('div', class_='bg coupon-row')
        
        for nombre in nombres:
            event_path = nombre.get('data-event-path', '')
            event_link = base_url + event_path
            is_nba_event = is_nba(event_path)
            is_nhl_event = is_nhl(event_path)

            # Define and clean the event name
            nombre_name = nombre['data-event-name'].replace(' vs ', ' - ').replace(' @ ', ' - ')
            nombre_name = clean_name(nombre_name)

            # Check if event is unique
            if nombre_name not in unique_events:
                unique_events.add(nombre_name)

                cuotas = {}

                # Find all 'td' elements with class 'price'
                cuota_elements = nombre.find_all('td', class_='price')

                for i, cuota in enumerate(cuota_elements, start=1):
                    market_type = cuota.get('data-market-type')
                    if market_type in ['RESULT', 'RESULT_2WAY']:
                        cuota_value = cuota.find('span', class_='selection-link').get_text()
                        cuotas[str(i)] = cuota_value

                # Proceed only if "cuotas" are found
                if cuotas:
                    # Swap the teams for NBA or NHL events
                    if is_nba_event or is_nhl_event:
                        nombre_name_parts = nombre_name.split(' - ')
                        if len(nombre_name_parts) == 2:
                            nombre_name = ' - '.join(nombre_name_parts[::-1])

                    # Swap odds for NBA events and NHL events, ensuring keys exist
                    if is_nba_event:
                        if '1' in cuotas and '2' in cuotas:
                            cuotas['1'], cuotas['2'] = cuotas['2'], cuotas['1']
                    elif is_nhl_event:
                        if '1' in cuotas and '3' in cuotas:
                            cuotas['1'], cuotas['3'] = cuotas['3'], cuotas['1']

                    archivo_salida.write(f"{nombre_name}\n")
                    for key, value in cuotas.items():
                        archivo_salida.write(f"  {key}: {value}\n")
                    # Write the event link
                    archivo_salida.write(f"link -> {event_link}\n")
                    archivo_salida.write("-----\n")

if __name__ == "__main__":
    scrape_marathonbet()