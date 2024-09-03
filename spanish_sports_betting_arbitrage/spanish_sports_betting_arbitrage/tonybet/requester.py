from requests_html import HTMLSession
import random
import time
from bs4 import BeautifulSoup
from pathlib import Path

start_time = time.time()

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent
session = HTMLSession()

with open(ROOT_DIR / 'tonybet/tonybet_links.html', 'w', encoding='utf-8') as file:
    file.write('')

# Clear the existing content in 'tonybet.html'
with open(ROOT_DIR / 'tonybet/tonybet_links.txt', 'r', encoding='utf-8') as file:
    for url in file:
        # Trim newline characters from the URL
        url = url.strip()

        # Perform the HTTP request with cookies
        response = session.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Randomize scrolldown and sleep_duration for each request
            scrolldown = random.randint(1, 6)
            sleep_duration = random.uniform(0.5, 2.0)
            
            # Render the JavaScript with randomized scrolldown and sleep
            response.html.render(sleep=sleep_duration, scrolldown=scrolldown)

            # Append the rendered HTML to 'tonybet_links.html'
            with open(ROOT_DIR / 'tonybet/tonybet_links.html', 'a', encoding='utf-8') as html_file:
                html_file.write(response.html.html + '\n\n')
        else:
            print(f'Error while fetching {url}. Response code: {response.status_code}')

# Read the original links from 'pokerstars_links.txt' into a set for comparison
with open(ROOT_DIR / 'tonybet/tonybet_links.txt', 'r', encoding='utf-8') as file:
    original_links = set(file.read().splitlines())

# Initialize a set for new, unique links
unique_links = set()

with open(ROOT_DIR / 'tonybet/tonybet_links.html', 'r', encoding='utf-8') as html_file:
    soup = BeautifulSoup(html_file, 'html.parser')
    links = soup.find_all(href=lambda x: x and x.startswith("/prematch/leagues"))

    for link in links:
        full_url = 'https://tonybet.es' + link['href']

        excluded_words = ['search', 'live', 'null', ]

        # Exclude links based on your criteria
        if any(word in full_url for word in excluded_words) or full_url in unique_links:
            continue

        # Count the number of segments in the URL
        num_segments = len(full_url.split('/')) - 2  # Adjust as per your URL structure
        
        # Check if the number of segments meets your criteria and the link is not in original_links
        if 10 > num_segments >= 1 and full_url not in original_links:
            unique_links.add(full_url)

# Write new unique links to 'tonybet_links_v2.txt'
with open(ROOT_DIR / 'tonybet/tonybet_links_v2.txt', 'w', encoding='utf-8') as file:
    for unique_link in unique_links:
        file.write(unique_link + '\n')

# Clear the existing content in 'bwin.html'
with open(ROOT_DIR / 'tonybet/tonybet.html', 'w', encoding='utf-8') as file:
    file.write('')

#  Read URLs from 'bwin_v2.html' and process each URL
with open(ROOT_DIR / 'tonybet/tonybet_links_v2.txt', 'r', encoding='utf-8') as file:
    for url in file:

        # Trim newline characters from the URL
        url = url.strip()

        # Perform the HTTP request with cookies
        response = session.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Randomize scrolldown and sleep_duration for each request
            scrolldown = random.randint(3, 6)
            sleep_duration = random.uniform(0.25, 0.75)
            
            # Render the JavaScript with randomized scrolldown and sleep
            response.html.render(sleep=sleep_duration, scrolldown=scrolldown)
            soup = BeautifulSoup(response.html.html, 'html.parser')

            with open(ROOT_DIR / 'tonybet/tonybet.html', 'a', encoding='utf-8') as html_file:
                    html_file.write(str(soup) + '\n')
        else:
            print(f'Error fetching {url}. Response code: {response.status_code}')

session.close()
end_time = time.time()
elapsed_time = end_time - start_time
minutes = (elapsed_time / 60)
print(f"Script executed in {elapsed_time:.2f} seconds.")
print(f"Script executed in {minutes:.2f} minutes.")
