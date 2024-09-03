from requests_html import HTMLSession
import random
import time
from bs4 import BeautifulSoup
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

start_time = time.time()

session = HTMLSession()
url = 'https://sports.bwin.es/es/sports?popup=sports'

cookies = {
    
    }

scrolldown = random.randint(1, 6)

sleep_duration = random.uniform(0.5, 2.0)

# Perform the HTTP request with cookies
response = session.get(url, cookies=cookies)

# Check if the request was successful
if response.status_code == 200:
    # Render the JavaScript with randomized scrolldown and sleep
    response.html.render(sleep=sleep_duration, scrolldown=scrolldown)
    
    # Parse the rendered HTML
    soup = BeautifulSoup(response.html.html, 'html.parser')

    # Save the rendered HTML to a file
    with open(ROOT_DIR / 'bwin/bwin.html', 'w', encoding='utf-8') as file:
        file.write(response.html.html)  # Use .html attribute to get the rendered HTML

    # Find all links that have got; 'href="/es/sports/'
    links = soup.find_all(href=lambda x: x and x.startswith("/es/sports/"))

    unique_links = set()  # To avoid duplicates

    with open(ROOT_DIR / 'bwin/bwin_links.txt', 'w', encoding='utf-8') as file:
        for link in links:
            full_url = 'https://sports.bwin.es' + link['href']

            excluded_words = ['directo', 'eventos', 'hoy', 'todas', 'apuestas',' bandy', 'los-']

            # Skip links containing 'eventos'
            if any(word in full_url for word in excluded_words) or full_url in unique_links:
                continue

            # Count the number of segments in the URL
            num_segments = len(full_url.split('/')) - 4  # -4 to account for https://bwin.sports/es/

            # Check if the number of segments is at least 3 (e.g., 'sports/1/2/')
            if 5 > num_segments >= 2:
                unique_links.add(full_url)

        # Write each unique link to the file
        for unique_link in unique_links:
            file.write(unique_link + '/apuestas' + '\n')
else:
    print(f'Error while making the request. Status code: {response.status_code}')

# Clear the existing content in 'bwin_links.html'
with open(ROOT_DIR / 'bwin/bwin_links.html', 'w', encoding='utf-8') as file:
    file.write('')

# Clear the existing content in 'bwin_links.html'
with open(ROOT_DIR / 'bwin/bwin_links.txt', 'r', encoding='utf-8') as file:
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
            with open(ROOT_DIR / 'bwin/bwin_links.html', 'a', encoding='utf-8') as html_file:
                html_file.write(response.html.html + '\n\n')
        else:
            print(f'Error while fetching {url}. Response code: {response.status_code}')

# Read the original links from 'pokerstars_links.txt' into a set for comparison
with open(ROOT_DIR / 'bwin/bwin_links.txt', 'r', encoding='utf-8') as file:
    original_links = set(file.read().splitlines())

# Initialize a set for new, unique links
unique_links = set()

with open(ROOT_DIR / 'bwin/bwin_links.html', 'r', encoding='utf-8') as html_file:
    soup = BeautifulSoup(html_file, 'html.parser')
    links = soup.find_all(href=lambda x: x and x.startswith("/es/sports/"))

    for link in links:
        full_url = 'https://sports.bwin.es' + link['href']

        excluded_words = ['mañana', 'directo', 'eventos', 'hoy', 'todas', ' bandy', 'los-', 'cupones']

        # Skip links containing 'eventos'
        if any(word in full_url for word in excluded_words) or full_url in original_links or full_url in unique_links:
            continue

        # Count the number of segments in the URL
        num_segments = len(full_url.split('/')) - 4  # -4 to account for https://bwin.sports/es/

        # Check if the number of segments is at least 3 (e.g., 'sports/1/2/')
        if 5 > num_segments >= 3: # 7 - 3
            unique_links.add(full_url)
            if any(full_url.startswith(original_link) for original_link in original_links):
                unique_links.add(full_url)

# Write new unique links to 'bwin_links_v2.txt'
with open(ROOT_DIR / 'bwin/bwin_links_v2.txt', 'w', encoding='utf-8') as file:
    for unique_link in unique_links:
        file.write(unique_link + '\n')

# Clear the existing content in 'bwin.html'
with open(ROOT_DIR / 'bwin/bwin.html', 'w', encoding='utf-8') as file:
    file.write('')

#  Read URLs from 'bwin_v2.html' and process each URL
with open(ROOT_DIR / 'bwin/bwin_links_v2.txt', 'r', encoding='utf-8') as file:
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

            # Append the rendered HTML to 'bwin.html'
            with open(ROOT_DIR / 'bwin/bwin.html', 'a', encoding='utf-8') as html_file:
                html_file.write(response.html.html + '\n')
        else:
            print(f'Error while fetching {url}. Response code: {response.status_code}')

session.close()
end_time = time.time()
elapsed_time = end_time - start_time
minutes = (elapsed_time / 60)
print(f"Script executed in {elapsed_time:.2f} seconds.")
print(f"Script executed in {minutes:.2f} minutes.")
