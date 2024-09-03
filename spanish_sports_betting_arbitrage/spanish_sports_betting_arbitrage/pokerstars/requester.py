import requests
from bs4 import BeautifulSoup
import time
import random
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent
url = 'https://www.pokerstars.es/sports/'

cookies = {

    }

response = requests.get(url, cookies=cookies)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    # Write the HTML to a file
    with open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'w', encoding='utf-8') as file:
        file.write(response.text)

    links = soup.find_all(href=lambda x: x and x.startswith("/sports/"))

    excluded_links = [
        "https://www.pokerstars.es/sports/my-bets/open/",
        "https://www.pokerstars.es/sports/isp/games/rules/",
        "https://www.pokerstars.es/sports/tennis/"
    ]

    # Words to exclude in the links
    excluded_words = ['jugadores', 'especiales', 'apuestas']

    unique_links = set()  # To avoid duplicates

    with open(ROOT_DIR / 'pokerstars/pokerstars_links.txt', 'w', encoding='utf-8') as file:
        for link in links:
            full_url = 'https://www.pokerstars.es' + link['href']

            # Skip links containing 'in-play' or excluded links
            if 'in-play' in full_url or any(full_url.startswith(excluded_link) for excluded_link in excluded_links):
                continue

            # Remove '/matches/' from the link
            full_url = full_url.replace('/matches', '')

            # Count the number of segments in the URL
            num_segments = len(full_url.split('/')) - 4  # -4 to account for https://www.pokerstars.es/

            # Check if the number of segments is at least 3 (e.g., 'sports/1/2/')
            if 5 > num_segments >= 3:
                unique_links.add(full_url)

        # Write each unique link to the file
        for unique_link in unique_links:
            file.write(unique_link + '\n')

            if '/sports/futbol/' in unique_link:
                modified_link = unique_link + 'competitions/'
                file.write(modified_link + '\n')  # Write the modified link beneath the original
            elif '/sports/carreras-de-caballos/' in unique_link:
                modified_link = unique_link + 'meetings/'
                file.write(modified_link + '\n')
else:
    print(f'Error while making the request. Response code: {response.status_code}')

# Clear the existing content in 'pokerstars_links.html'
with open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'w', encoding='utf-8') as file:
    file.write('')

# Read URLs from 'pokerstars_links.txt' and process each URL
with open(ROOT_DIR / 'pokerstars/pokerstars_links.txt', 'r', encoding='utf-8') as file:
    for url in file:
        # Sleep for a random duration between requests
        time.sleep(random.uniform(2.55, 5.35))

        # Send the request to the URL
        response = requests.get(url.strip(), cookies=cookies)

        # Check if the request was successful
        if response.status_code == 200:
            # Append the HTML content to 'pokerstars_links.html'
            with open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'a', encoding='utf-8') as html_file:
                html_file.write(response.text + '\n')
        else:
            print(f'Error while fetching {url}. Response code: {response.status_code}')

# Read the original links from 'pokerstars_links.txt' into a set for comparison
with open(ROOT_DIR / 'pokerstars/pokerstars_links.txt', 'r', encoding='utf-8') as file:
    original_links = set(file.read().splitlines())

# Initialize a set for new, unique links
unique_links = set()

with open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'r', encoding='utf-8') as html_file:
    soup = BeautifulSoup(html_file, 'html.parser')
    links = soup.find_all(href=lambda x: x and x.startswith("/sports/"))

    for link in links:
        full_url = 'https://www.pokerstars.es' + link['href']

        # Skip links containing 'in-play', excluded links, original links, or specific words
        if ('in-play' in full_url or 
            any(full_url.startswith(excluded_link) for excluded_link in excluded_links) or 
            full_url in original_links or
            any(word in full_url for word in excluded_words)):
            continue

        # Remove '/matches/' from the link
        full_url = full_url.replace('/matches', '')

        # Count the number of segments in the URL
        num_segments = len(full_url.split('/')) - 4

        # Check if the number of segments is at least 4, but no more than 6
        if 6 > num_segments >= 4:
            # Check if the link is an expansion of the original links
            if any(full_url.startswith(original_link) for original_link in original_links):
                unique_links.add(full_url)

# Write new unique links to 'pokerstars_links_v2.txt'
with open(ROOT_DIR / 'pokerstars/pokerstars_links_v2.txt', 'w', encoding='utf-8') as file:
    for unique_link in unique_links:
        file.write(unique_link + '\n')

# Clear the existing content in 'pokerstars.html'
with open(ROOT_DIR / 'pokerstars/pokerstars.html', 'w', encoding='utf-8') as file:
    file.write('')

# Read URLs from 'pokerstars_links_v2.txt' and process each URL
with open(ROOT_DIR / 'pokerstars/pokerstars_links_v2.txt', 'r', encoding='utf-8') as file:
    for url in file:
        # Sleep for a random duration between requests
        time.sleep(random.uniform(2.45, 3.35))

        # Send the request to the URL
        response = requests.get(url.strip(), cookies=cookies)

        # Check if the request was successful
        if response.status_code == 200:
            # Append the HTML content to 'pokerstars.html'
            with open(ROOT_DIR / 'pokerstars/pokerstars.html', 'a', encoding='utf-8') as html_file:
                html_file.write(response.text + '\n')
        else:
            print(f'Error while fetching {url}. Response code: {response.status_code}')
            