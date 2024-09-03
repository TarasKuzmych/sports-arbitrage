import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

url = 'https://apuestas.kirolbet.es/'

cookies = {
    
    }
response = requests.get(url, cookies=cookies)

if response.status_code == 200:

    soup = BeautifulSoup(response.text, 'html.parser')

    with open(ROOT_DIR / 'kirolbet/kirolbet_links.html', 'w', encoding='utf-8') as file:
        file.write(response.text)
else:
    print(f'Error al realizar la solicitud. Código de respuesta: {response.status_code}')


# Read the HTML file
with open(ROOT_DIR / 'kirolbet/kirolbet_links.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

# Find all <li> elements with the specified class
li_elements = soup.find_all('li', class_='dcjq-parent-li ksAccordion-li')

# Extract the IDs and create URLs
urls = []
for li in li_elements:
    # Extract the ID from either the <a> tag or the .ksAccordion-ajax-data div
    a_tag = li.find('a', class_='dcjq-parent')
    div_tag = li.find('div', class_='ksAccordion-ajax-data')
    
    if a_tag and a_tag.has_attr('id'):
        sport_id = a_tag['id']
    elif div_tag:
        sport_id = div_tag.text.split('=')[-1].strip()
    else:
        continue  # Skip if no ID found

    # Format the URL and add it to the list
    url = f'https://apuestas.kirolbet.es/esp/Sport/Deporte/{sport_id}'
    urls.append(url)

# Write the URLs to a file
with open(ROOT_DIR / 'kirolbet/kirolbet_links.txt', 'w', encoding='utf-8') as file:
    for url in urls:
        file.write(url + '\n')
        