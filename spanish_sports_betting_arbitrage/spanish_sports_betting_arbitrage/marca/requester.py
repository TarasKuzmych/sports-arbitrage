import requests
import time
import random
from bs4 import BeautifulSoup
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

url = 'https://deportes.marcaapuestas.es/es/apuestas-futbol'
cookies = {
    
    }

response = requests.get(url, cookies=cookies)

if response.status_code == 200:
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all 'li' elements with class 'expander'
    expanders = soup.find_all('li', class_='expander')
    
    # Filter out the 'Apuestas a Largo Plazo' expander
    valid_expanders = [expander for expander in expanders if 'Apuestas a Largo Plazo' not in expander.text]
    
    # Find all valid links
    links = []
    for expander in valid_expanders:
        for a in expander.find_all('a', href=True):
            link = 'https://deportes.marcaapuestas.es' + a['href']
            # Check if link contains 'Ganador' or 'Winner' and is not already in the list
            link_final = link.replace('%28', '(').replace('%29', ')')
            if 'Ganador' not in link and 'Winner' not in link and 'Apuesta-a-largo-plazo' not in link and 'Alcanza-Final' not in link and 'Nombre-de-los-Finalistas' not in link and link not in links:
                links.append(link_final)

    # Save the links to a file
    with open(ROOT_DIR / 'marca/marca_links.txt', 'w') as file:
        file.write('https://deportes.marcaapuestas.es/es' + '\n')
        for link in links:
            file.write(link + '\n')

    with open(ROOT_DIR / 'marca/marca_links.html', 'w', encoding='utf-8') as file:
        file.write(response.text)

    combined_html = ""
    n = 900

    # Visit each of the first n links (or fewer if there aren't enough)
    for link in links[:n]:
        # Wait for a random time between 1.51 and 6.23 seconds
        time.sleep(random.uniform(1.51, 3.23))

        link_response = requests.get(link, cookies=cookies)
        if link_response.status_code == 200:
            # Append the HTML content of each link to the combined_html string
            combined_html += link_response.text

    # Save the combined HTML of the first 10 links to a single file
    with open(ROOT_DIR / 'marca/marca.html', 'w', encoding='utf-8') as file:
        file.write(combined_html)

else:
    print(f'Error while making the request. Error code: {response.status_code}')
