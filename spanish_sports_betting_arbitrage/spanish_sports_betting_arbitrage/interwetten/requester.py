import requests
import random
import time
from bs4 import BeautifulSoup
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

url = 'https://www.interwetten.es'

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
