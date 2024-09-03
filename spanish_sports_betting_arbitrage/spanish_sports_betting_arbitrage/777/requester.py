from requests_html import HTMLSession
import random
import time
from bs4 import BeautifulSoup
from pathlib import Path

start_time = time.time()

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

session = HTMLSession()
url = 'https://www.bet777.es/'

cookies = {

}

scrolldown = random.randint(1, 6)

# Randomize sleep duration between requests to simulate human behavior
sleep_duration = random.uniform(0.5, 2.0)

# Perform the HTTP request with cookies
response = session.get(url, cookies=cookies)

# Check if the request was successful
if response.status_code == 200:
    # Render the JavaScript with randomized scrolldown and sleep
    response.html.render(sleep=sleep_duration, scrolldown=scrolldown)

    # Parse the rendered HTML
    soup = BeautifulSoup(response.html.html, 'html.parser')

    with open(ROOT_DIR / '777/777.html', 'w', encoding='utf-8') as file:
        file.write(response.html.html)

    links = soup.find_all(href=lambda x: x and x.startswith("/"))

    unique_links = set()  # To avoid duplicates

    with open(ROOT_DIR / '777/777_links.txt', 'w', encoding='utf-8') as file:
        for link in links:
            full_url = 'https://www.bet777.es' + link['href']

            excluded_words = ['directo', 'ayuda', 'search', '_nuxt', 'promociones', 'resultados', 'match']

            if any(word in full_url for word in excluded_words) or 'sports' in full_url.split('/') or full_url in unique_links:
                continue

             # Count the number of segments in the URL
            num_segments = len(full_url.split('/')) - 4  # -4 to account for https://bwin.sports/es/

            # Check if the number of segments is at least 3 (e.g., 'sports/1/2/')
            if 2 > num_segments >= 1:
                unique_links.add(full_url)

        # Write each unique link to the file
        for unique_link in unique_links:
            file.write(unique_link + '\n')
else:
    print(f'Error al realizar la solicitud. Código de respuesta: {response.status_code}')

# Clear the existing content in '777_links.html'
with open(ROOT_DIR / '777/777_links.html', 'w', encoding='utf-8') as file:
    file.write('')

# Clear the existing content in 'bwin_links.html'
with open(ROOT_DIR / '777/777_links.txt', 'r', encoding='utf-8') as file:
    for url in file:
        # Trim newline characters from the URL
        url = url.strip()

        # Perform the HTTP request with cookies
        response = session.get(url, cookies=cookies)

        # Check if the request was successful
        if response.status_code == 200:
            # Randomize scrolldown and sleep_duration for each request
            scrolldown = random.randint(1, 6)
            sleep_duration = random.uniform(0.5, 2.0)
            
            # Render the JavaScript with randomized scrolldown and sleep
            response.html.render(sleep=sleep_duration, scrolldown=scrolldown)

            # Append the rendered HTML to 'bwin_links.html'
            with open(ROOT_DIR / '777/777_links.html', 'a', encoding='utf-8') as html_file:
                html_file.write(response.html.html + '\n\n')
        else:
            print(f'Error while fetching {url}. Response code: {response.status_code}')

# Read the original links from 'pokerstars_links.txt' into a set for comparison
with open(ROOT_DIR / '777/777_links.txt', 'r', encoding='utf-8') as file:
    original_links = set(file.read().splitlines())

# Initialize a set for new, unique links
unique_links = set()

with open(ROOT_DIR / '777/777_links.html', 'r', encoding='utf-8') as html_file:
    soup = BeautifulSoup(html_file, 'html.parser')
    links = soup.find_all(href=lambda x: x and x.startswith("/"))

    for link in links:
        full_url = 'https://www.bet777.es' + link['href']

        excluded_words = ['bola-de-piso', 'directo', 'ayuda', 'search', '_nuxt', 'promociones', 'resultados', 'match', 'outrights', 'event', 'resultado']

        # Exclude links based on your criteria
        if any(word in full_url for word in excluded_words) or 'sports' in full_url.split('/') or full_url in unique_links:
            continue

        # Count the number of segments in the URL
        num_segments = len(full_url.split('/')) - 4  # Adjust as per your URL structure
        
        # Check if the number of segments meets your criteria and the link is not in original_links
        if 10 > num_segments >= 1 and full_url not in original_links:
            unique_links.add(full_url)

# Write new unique links to '777_links_v2.txt'
with open(ROOT_DIR / '777/777_links_v2.txt', 'w', encoding='utf-8') as file:
    for unique_link in unique_links:
        file.write(unique_link + '\n')

# Clear the existing content in '777.html'
with open(ROOT_DIR / '777/777.html', 'w', encoding='utf-8') as file:
    file.write('')

#  Read URLs from '777_v2.html' and process each URL
with open(ROOT_DIR / '777/777_links_v2.txt', 'r', encoding='utf-8') as file:
    for url in file:

        # Trim newline characters from the URL
        url = url.strip()

        # Perform the HTTP request with cookies
        response = session.get(url, cookies=cookies)

        # Check if the request was successful
        if response.status_code == 200:
            # Randomize scrolldown and sleep_duration for each request
            scrolldown = random.randint(3, 6)
            sleep_duration = random.uniform(0.25, 0.75)
            
            # Render the JavaScript with randomized scrolldown and sleep
            response.html.render(sleep=sleep_duration, scrolldown=scrolldown)

            # Append the rendered HTML to '777.html'
            with open(ROOT_DIR / '777/777.html', 'a', encoding='utf-8') as html_file:
                html_file.write(response.html.html + '\n')
        else:
            print(f'Error while fetching {url}. Response code: {response.status_code}')

session.close()
end_time = time.time()
elapsed_time = end_time - start_time
minutes = (elapsed_time / 60)
print(f"Script executed in {elapsed_time:.2f} seconds.")
print(f"Script executed in {minutes:.2f} minutes.")
