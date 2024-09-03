import requests
from bs4 import BeautifulSoup
import random
import time
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
    to_remove = ['CSD', 'Atl', 'Ind', 'S.A', 'SSD', 'Baloncesto', 'Hotspur', 'GF', 'BM', 'Zacatecoluca', 'LUK', 'Women', 'Atsmon Playgrounds', 'Rio', 'Basket', 'WKS', 'Cazoo', 'Vitoria Gasteiz', 'Femenino', 'NIS', 'OPAP Athens', 'AD', 'Cs', 'OK', 'KK', 'FC', 'CF', 'CD', 'EC', 'SE', 'MG', 'FK', 'KF', 'AC', 'BK', 'TC', 'NK', 'SD', 'RJ', 'MT', 'BA', 'GO', 'SP', 'CE', 'SC', 'SV', 'RC', 'GC', 'AS', 'SS', 'UD', 'SK', 'CA', 'SL', 'AFC', 'CSC', 'BSC', 'RSC', 'GFC', 'LFC', 'SFC', 'RFC', 'VfL', 'VfB', 'FSV', 'SVW', 'JFC', 'DFC', 'HFC', 'Utd', 'SV', 'RCD', 'FBC', 'PFC', 'TSV', 'EFC', 'CFC', 'BFC', 'JSC', 'OSC', 'RRC', 'CSC', 'GSC', 'HSC', 'MSC', 'SSC', 'VSC', 'WSC', 'ZSC', 'AZ', 'PSV', 'FCZ', 'FCS', 'FCT', 'RKC', 'NAC', 'VVV', 'PEC', 'FCM', 'US', 'AJA', 'AZ', 'RBC', 'TFC', 'WFC', 'IFK', 'GIF', 'BIF', 'AIF', 'MFF', 'AIK', 'DIF', 'HIF', 'ÖFK', 'ÖSK', 'ÖIS', 'GIF', 'AaB', 'BIF', 'FCK', 'OB', 'VB', 'AGF', 'RFC', 'JJK', 'HJK', 'HIFK', 'SJK', 'KTP', 'KPV', 'PS', 'KuPS', 'MYPA', 'VPS', 'FF', 'IF', 'IK', 'BKV', 'BSV', 'B1901', 'B1903', 'B1909', 'B1913', 'KB', 'AB', 'VB', 'LFC', 'BC', 'CB', 'Lfc']

    # Modify the name by removing prefixes and suffixes at the beginning or end
    for item in to_remove:
        # Regular expression for prefix or suffix as a separate word
        word_pattern = r'\b' + re.escape(item) + r'\b'
        name = re.sub(word_pattern, '', name, flags=re.IGNORECASE)

    # Trim and remove extra spaces
    name = ' '.join(name.split())
    return name


def scrape_interwetten():
    url = 'https://www.interwetten.es/es/apuestas-deportivas'

    cookies = {
    }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        with open(ROOT_DIR / 'interwetten/interwetten_links.html', 'w', encoding='utf-8') as file:
            file.write(response.text)
    else:
        print(f'Error al realizar la solicitud. Código de respuesta: {response.status_code}')

    with open(ROOT_DIR / 'interwetten/interwetten_links.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')

    # Use a set to store unique links
    unique_hrefs = set()

    hrefs = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('/es/apuestas-deportivas/l/') and 'especial' not in href and 'especiales' not in href:
            unique_hrefs.add(f'{url}{href}')

    # Write the URLs to a file
    with open(ROOT_DIR / 'interwetten/interwetten_links.txt', 'w', encoding='utf-8') as file:
        for href in unique_hrefs:
            file.write(f'{href}\n')

    with open(ROOT_DIR / 'interwetten/interwetten.html', 'w', encoding='utf-8') as file:
        file.write('')

    # Read the links from 'interwetten_links.txt'
    with open(ROOT_DIR / 'interwetten/interwetten_links.txt', 'r', encoding='utf-8') as file:
        links = file.read().splitlines()

    # Iterate over each link
    for link in links:
        try:
            # Send HTTP request to the link
            response = requests.get(link)
            if response.status_code == 200:
                # Append the HTML content to 'interwetten.html'
                with open(ROOT_DIR / 'interwetten/interwetten.html', 'a', encoding='utf-8') as file:
                    file.write(response.text + "\n\n")
            else:
                print(f'Error accessing {link}: Status code {response.status_code}')
        except Exception as e:
            print(f'An error occurred while accessing {link}: {e}')
        # Wait for a random time between 2.55 and 4.35 seconds
        time.sleep(random.uniform(2.55, 4.35))

    # Your complete HTML file here
    file_path = ROOT_DIR / 'interwetten/interwetten.html'
    archivo_resultados = ROOT_DIR / 'interwetten/interwetten.txt'

    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Create the BeautifulSoup object
    soup = BeautifulSoup(html_content, 'html.parser')
    base_url = 'https://www.interwetten.es'

    # Open the output file for writing
    with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        for event_row in soup.find_all('tr', class_=lambda x: x and x in ['odd', 'even']):
            # Skip rows with 'Handicap' in any nested 'tr' element's 'data-betting' attribute
            if any('Handicap' in nested_tr.get('data-betting', '') for nested_tr in event_row.find_all('tr', recursive=True)):
                continue

            participants = [p.get_text() for p in event_row.find_all('span', class_='tip-name', itemprop='name') if p.get_text() != "Empate"]
            if not (2 <= len(participants) <= 3):
                continue  # Skip if not the correct number of participants
            
            # Clean the participants' names
            participants_clean = [participant.replace(',', '') for participant in participants]

            # Construct event title
            event_title = ' - '.join(participants_clean)
            event = clean_name(event_title)  # Assuming `clean_name` is a function defined elsewhere

            # Find the event link
            event_link_element = event_row.find('a', class_='url', href=True)
            event_link = base_url + event_link_element['href'] if event_link_element else "Link not found"

            # Write event and odds to file
            archivo_salida.write(event + "\n")
            counter = 1
            for betting_offer in event_row.find_all('td', class_='BETTINGOFFER'):
                odds = betting_offer.find('strong').text.strip().replace(',', '.')
                archivo_salida.write(f"  {counter}: {odds}\n")
                counter += 1
            
            # Write event link to file
            archivo_salida.write(f"link -> {event_link}\n")
            archivo_salida.write("-----\n")

if __name__ == "__main__":
    scrape_interwetten()