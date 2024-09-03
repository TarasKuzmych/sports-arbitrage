from requests_html import HTMLSession
import random
import time
from bs4 import BeautifulSoup
from pathlib import Path

start_time = time.time()

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

session = HTMLSession()
url = 'https://www.dafabet.es/es/sports'

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

    with open(ROOT_DIR / 'dafabet/dafabet.html', 'w', encoding='utf-8') as file:
        file.write(response.html.html)  # Use .html attribute to get the rendered HTML

    links = soup.find_all(href=lambda x: x and x.startswith("/es/sports/"))

    unique_links = set()  # To avoid duplicates

    with open(ROOT_DIR / 'dafabet/dafabet_links.txt', 'w', encoding='utf-8') as file:
        for link in links:
            full_url = 'https://www.dafabet.es' + link['href']

            excluded_words = ['event', 'search', 'match', 'live', 'outrights', 'daily', 'odds', 'booster']

            if any(word in full_url for word in excluded_words) or full_url in unique_links:
                    continue

            # Count the number of segments in the URL
            num_segments = len(full_url.split('/')) - 4  # -4 to account for https://www.dafabet.es/sports/

            # Check if the number of segments is at least 3 (e.g., 'sports/1/2/')
            if 5 > num_segments >= 4:
                unique_links.add(full_url)

        # Write each unique link to the file
        for unique_link in unique_links:
            file.write(unique_link + '\n')
else:
    print(f'Error while making the request. Status code: {response.status_code}')

# Clear the existing content in 'dafabet.html'
with open(ROOT_DIR / 'dafabet/dafabet.html', 'w', encoding='utf-8') as file:
    file.write('')

#  Read URLs from 'dafabet_links.txt' and process each URL
with open(ROOT_DIR / 'dafabet/dafabet_links.txt', 'r', encoding='utf-8') as file:
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

            # Append the rendered HTML to 'dafabet.html'
            with open(ROOT_DIR / 'dafabet/dafabet.html', 'a', encoding='utf-8') as html_file:
                html_file.write(response.html.html + '\n')
        else:
            print(f'Error while fetching {url}. Response code: {response.status_code}')

session.close()
end_time = time.time()
elapsed_time = end_time - start_time
minutes = (elapsed_time / 60)
print(f"Script executed in {elapsed_time:.2f} seconds.")
print(f"Script executed in {minutes:.2f} minutes.")
