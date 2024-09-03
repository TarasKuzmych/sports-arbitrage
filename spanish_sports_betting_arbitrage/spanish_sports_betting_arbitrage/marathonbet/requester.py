import requests
import time
import random
from bs4 import BeautifulSoup
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

url = 'https://www.marathonbet.es/es/'

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