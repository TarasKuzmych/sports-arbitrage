import requests
import re
import json
from bs4 import BeautifulSoup
import random
import time
import unicodedata
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


def scrape_betfair():
    # Load URLs from the original file
    with open(ROOT_DIR / 'betfair/betfair_links.txt', 'r') as url_file:
        urls = url_file.read().splitlines()

    cookies = {

    }

    hrefs = []
    archivo_salida = ROOT_DIR / 'betfair/betfair_links.html'
    combined_html_content = ''
    for url in urls:
        # Add a random delay between requests
        delay = random.uniform(4.46, 6.37)
        time.sleep(delay)

        response = requests.get(url, cookies=cookies)

        if response.status_code == 200:
            # Save the HTML content to a file
            with open(archivo_salida, 'w', encoding='utf-8') as html_file:
                html_file.write(response.text)

            # Read the HTML content from the file
            with open(archivo_salida, 'r', encoding='utf-8') as html_file:
                html_content = html_file.read()

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the script tag containing 'platformConfig'
            script_tag = soup.find('script', string=re.compile(r'^\s*platformConfig', re.M))

            if script_tag:
                # Extract the JSON-like string
                json_str = re.search(r'platformConfig = ({.*?});', script_tag.text, re.DOTALL).group(1)

                # Parse the JSON string
                platform_config = json.loads(json_str)

                # Extract sport name from the URL
                match = re.search(r'/sport/([^/?]+)', url)
                if match:
                    sport_name = match.group(1)

                    # Extract HTML snippets from the config
                    html_snippets = []
                    for instruction in platform_config.get("page", {}).get("config", {}).get("instructions", []):
                        if "html" in instruction.get("arguments", {}):
                            html_snippets.append(instruction["arguments"]["html"])

                    # Extract hrefs with the original sport name
                    for snippet in html_snippets:
                        snippet_soup = BeautifulSoup(snippet, 'html.parser')
                        for a_tag in snippet_soup.find_all('a', href=re.compile(f'^/sport/{sport_name}/')):
                            hrefs.append(a_tag['href'])

        else:
            print(f'Error while making the request. Response code: {response.status_code}')

    # Write the combined HTML content to 'betfair_links.html'
    with open(archivo_salida, 'w', encoding='utf-8') as html_file:
        html_file.write(combined_html_content)

    # Write the hrefs to 'betfair_links_v2.txt'
    with open(ROOT_DIR / 'betfair/betfair_links_v2.txt', 'w') as file:
        for href in hrefs:
            file.write('https://www.betfair.es' + href + '\n')

    # File to store the combined HTML content
    output_file_v2 = ROOT_DIR / 'betfair/betfair.html'

    # Read URLs from 'betfair_links_v2.txt'
    with open(ROOT_DIR / 'betfair/betfair_links_v2.txt', 'r') as file:
        new_urls = file.read().splitlines()

    # Open and close the file in write mode to clear its contents
    with open(output_file_v2, 'w', encoding='utf-8') as html_file_v2:
        pass

    for new_url in new_urls:
        # Random delay between requests
        delay = random.uniform(2.57, 3.57)
        time.sleep(delay)

        response = requests.get(new_url, cookies=cookies)

        # Check if the request was successful
        if response.status_code == 200:
            # Append the HTML content to 'betfair.html'
            with open(output_file_v2, 'a', encoding='utf-8') as html_file_v2:
                html_file_v2.write(response.text + '\n')
        else:
            print(f'Error in request. Response code: {response.status_code}')

    ruta_archivo = ROOT_DIR / 'betfair/betfair.html'
    archivo_resultados = ROOT_DIR / 'betfair/betfair.txt'

    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        html_content = archivo.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    events = []
    processed_events = set()

    base_url = "https://www.betfair.es"

    # Loop through each event
    for event_info in soup.find_all("div", class_="event-information"):
        if 'ui-inplay' in event_info['class']:
            continue

        is_ice_hockey = any("ICE_HOCKEY" in a.get('data-sport', '') for a in event_info.find_all(True))

        event = {"teams": [], "odds": [], "link": ""}

        event_name_info = event_info.find("div", class_="event-name-info")
        if event_name_info:
            teams = event_name_info.find_all("span", class_=("team-name"))
            event_title = ' - '.join([team.get_text(strip=True) for team in teams])
            cleaned_event_title = clean_name(event_title)
            event["teams"] = cleaned_event_title.split(' - ')

        runner_lists = event_info.find_all("ul", class_="runner-list-selections")
        if runner_lists:
            last_runner_list = runner_lists[-1]
            selections = last_runner_list.find_all("li", class_="selection")

            if is_ice_hockey and len(selections) != 3:
                continue

            for selection in selections:
                outcome = selection.find("span", class_="ui-runner-price")
                if outcome:
                    event["odds"].append(outcome.get_text(strip=True))

        event_link = event_info.find("a", class_="ui-nav markets-number-arrow ui-top event-link ui-gtm-click")
        if event_link and 'href' in event_link.attrs:
            event["link"] = base_url + event_link['href']

        # Check if the odds are complete and valid
        if all(event["odds"]):
            event_id = " - ".join(event["teams"]) + " | " + " - ".join(event["odds"])
            if event_id not in processed_events:
                processed_events.add(event_id)
                events.append(event)

    with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        for e in events:
            archivo_salida.write(" - ".join(e["teams"]) + "\n")
            for i, odd in enumerate(e["odds"], start=1):
                archivo_salida.write(f"  {i}: {odd}\n")
            archivo_salida.write(f"link -> {e['link']}\n")
            archivo_salida.write("-" * 5 + "\n")

if __name__ == "__main__":
    scrape_betfair()