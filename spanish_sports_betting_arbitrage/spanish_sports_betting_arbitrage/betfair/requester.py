import requests
import re
import json
from bs4 import BeautifulSoup
import random
import time
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

# Load the list of URLs from 'betfair_links.txt'
with open(ROOT_DIR / 'betfair/betfair_links.txt', 'r') as url_file:
    urls = url_file.read().splitlines()

cookies = {
}

archivo_salida = ROOT_DIR / 'betfair/betfair_links.html'

# Initialize an empty list to store hrefs
hrefs = []

# Initialize an empty string to store the combined HTML content
combined_html_content = ''

for url in urls:
    # Add a random delay between requests
    delay = random.uniform(2.57, 3.37)
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
    delay = random.uniform(1.57, 2.37)
    time.sleep(delay)

    response = requests.get(new_url, cookies=cookies)

    # Check if the request was successful
    if response.status_code == 200:
        # Append the HTML content to 'betfair_v2.html'
        with open(output_file_v2, 'a', encoding='utf-8') as html_file_v2:
            html_file_v2.write(response.text + '\n')
    else:
        print(f'Error while making the request. Response code: {response.status_code}')