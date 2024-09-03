import requests
from bs4 import BeautifulSoup
import time
import random
import re
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent
url = 'https://www.zebet.es'

cookies = {
    
    }

response = requests.get(url, cookies=cookies)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    with open(ROOT_DIR / 'zebet/zebet_links.html', 'w', encoding='utf-8') as file:
        file.write(response.text)
else:
    print(f'Error al realizar la solicitud. Código de respuesta: {response.status_code}')

# Reading and parsing 'zebet_links.html'
with open(ROOT_DIR / 'zebet/zebet_links.html', 'r', encoding='utf-8') as file:
    soup = BeautifulSoup(file, 'html.parser')

    # Find all <a> tags within <li> tags where href starts with '/es/competition'
    links = soup.find_all('a', href=re.compile('^/es/competition'))

    # Using a set to store unique links
    unique_links = set()

    # Write the complete URLs to 'zebet_links.txt', avoiding duplicates
    with open(ROOT_DIR / 'zebet/zebet_links.txt', 'w', encoding='utf-8') as outfile:
        for link in links:
            full_url = url + link['href']
            if full_url not in unique_links:
                outfile.write(full_url + '\n')
                unique_links.add(full_url)

with open(ROOT_DIR / 'zebet/zebet.html', 'w', encoding='utf-8') as file:
    file.write('')

# Read the links from 'zebet_links.txt' and process each link
with open(ROOT_DIR / 'zebet/zebet_links.txt', 'r', encoding='utf-8') as link_file:
    for url in link_file:
        url = url.strip()
        try:
            # Random delay between requests
            time.sleep(random.uniform(2.55, 4.35))
            response = requests.get(url, cookies=cookies)

            # Check if the request was successful (response code 200)
            if response.status_code == 200:
                with open(ROOT_DIR / 'zebet/zebet.html', 'a', encoding='utf-8') as html_file:
                    # Append the HTML content to 'zebet.html'
                    html_file.write(response.text + '\n')
            else:
                print(f'Error while making the request to {url}. Response code: {response.status_code}')
        except Exception as e:
            print(f'An error occurred while processing {url}: {e}')
