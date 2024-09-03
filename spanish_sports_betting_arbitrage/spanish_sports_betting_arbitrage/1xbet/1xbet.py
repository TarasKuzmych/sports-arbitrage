from pyppeteer import launch, errors as pyppeteer_errors
from bs4 import BeautifulSoup
import unicodedata
import aiofiles
import asyncio
import random
import time
import time
import re
from pathlib import Path

# Shared utility functions

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent
def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('ASCII')

women_categories = {
    '(F)': 'Femenino', 'Women': 'Femenino', 'women': 'Femenino', 'Femenino': 'Femenino', ' (W) ': 'Femenino', 'Ladies': 'Femenino'
}
age_categories = {
    'Sub 18': 'U18', 'SUB 18': 'U18', 'sub 18': 'U18', 'SUB-18': 'U18', 'sub-18': 'U18', 'u18': 'U18', 'Sub-18': 'U18',
    'Sub 20': 'U20', 'SUB 20': 'U20', 'sub 20': 'U20', 'SUB-20': 'U20', 'sub-20': 'U20', 'u20': 'U20', 'Sub-20': 'U20', 
    'Sub 21': 'U21', 'SUB 21': 'U21', 'sub 21': 'U21', 'SUB-21': 'U21', 'sub-21': 'U21', 'u21': 'U21', 'Sub-21': 'U21',
    'Sub 22': 'U22', 'SUB 22': 'U22', 'sub 22': 'U22', 'SUB-22': 'U22', 'sub-22': 'U22', 'u22': 'U22', 'Sub-22': 'U22',
    'Sub 23': 'U23', 'SUB 23': 'U23', 'sub 23': 'U23', 'SUB-23': 'U23', 'sub-23': 'U23', 'u23': 'U23', 'Sub-23': 'U23',
    'Sub 25': 'U25', 'SUB 25': 'U25', 'sub 25': 'U25', 'SUB-25': 'U25', 'sub-25': 'U25', 'u25': 'U25', 'Sub-25': 'U25'
}

def standardize_categories(event_name, category_mapping):
    # First handle the '(W)' case specifically
    event_name = re.sub(r'\(W\)', 'Femenino', event_name, flags=re.IGNORECASE)
    event_name = re.sub(r'\(F\)', 'Femenino', event_name, flags=re.IGNORECASE)

    # Split the event name into parts to handle each team separately
    parts = event_name.split(' - ')
    standardized_parts = []

    for part in parts:
        # Check and replace each variation with the standard term
        for variation, standard in category_mapping.items():
            # Skip the specific case that has already been handled
            if variation == '(W)' or variation == '(F)':
                continue
            
            # Replace the variation with the standard term if it's not already there
            if standard not in part:
                part = re.sub(r'\b' + re.escape(variation) + r'\b', standard, part, flags=re.IGNORECASE)
        
        # Clean up any repeated standard terms and trim whitespace
        part = re.sub(r'\b' + re.escape(standard) + r'\b', standard, part)  # Apply the standard term
        part = ' '.join(part.split())  # Remove extra spaces
        standardized_parts.append(part)

    # Rejoin the standardized parts
    return ' - '.join(standardized_parts)

def clean_name(name):
    name = remove_accents(name)

    # Extract age category if present
    age_category = None
    for category in age_categories.values():
        if category in name:
            age_category = category
            break

    name = standardize_categories(name, age_categories)
    name = standardize_categories(name, women_categories)

    # Remove all occurrences of age categories
    for category in age_categories.values():
        name = re.sub(rf'\b{category}\b', '', name)

    name = re.sub(r'\((?!W\))[^)]*\)', '', name)

    # Complete list of prefixes and suffixes to remove
    to_remove = ['@ ', 'RB', 'HSG', 'MVV', 'JC', 'Basquet', 'CSD', 'Atl', 'Ind', 'S.A', 'SSD', 'Baloncesto', 'GF', 'BM', 'LUK', 'Rio', 'Basket', 'WKS', 'Cazoo',  'NIS', 'AD', 'Cs', 'OK', 'KK', 'FC', 'CF', 'CD', 'EC', 'SE', 'MG', 'FK', 'KF', 'AC', 'BK', 'TC', 'NK', 'SD', 'RJ', 'MT', 'BA', 'GO', 'SP', 'CE', 'SC', 'SV', 'RC', 'GC', 'AS', 'SS', 'UD', 'SK', 'CA', 'SL', 'AFC', 'CSC', 'BSC', 'RSC', 'GFC', 'LFC', 'SFC', 'RFC', 'VfL', 'VfB', 'FSV', 'SVW', 'JFC', 'DFC', 'HFC', 'Utd', 'SV', 'RCD', 'FBC', 'PFC', 'TSV', 'EFC', 'CFC', 'BFC', 'JSC', 'OSC', 'RRC', 'CSC', 'GSC', 'HSC', 'MSC', 'SSC', 'VSC', 'WSC', 'ZSC', 'AZ', 'PSV', 'FCZ', 'FCS', 'FCT', 'RKC', 'NAC', 'VVV', 'PEC', 'FCM', 'US', 'AJA', 'AZ', 'RBC', 'TFC', 'WFC', 'IFK', 'GIF', 'BIF', 'AIF', 'MFF', 'AIK', 'DIF', 'HIF', 'ÖFK', 'ÖSK', 'ÖIS', 'GIF', 'AaB', 'BIF', 'FCK', 'OB', 'VB', 'AGF', 'RFC', 'JJK', 'HJK', 'HIFK', 'SJK', 'KTP', 'KPV', 'PS', 'KuPS', 'MYPA', 'VPS', 'FF', 'IF', 'IK', 'BKV', 'BSV', 'B1901', 'B1903', 'B1909', 'B1913', 'KB', 'AB', 'VB', 'LFC', 'BC', 'CB', 'Lfc']

    # Remove '@' symbol if it's at the start of the name
    name = re.sub(r'^@ ?', '', name)

    # Modify the name by removing prefixes and suffixes at the beginning or end
    for item in to_remove:
        word_pattern = r'\b' + re.escape(item) + r'\b'
        name = re.sub(word_pattern, '', name, flags=re.IGNORECASE)

    # Reapply the extracted age category uniformly to both teams
    if age_category:
        name = re.sub(r'(^.*?)( - )', rf'\1 {age_category}\2', name)
        team1, separator, team2 = name.partition(' - ')
        if age_category not in team2:
            team2 = f'{team2} {age_category}'
        name = f'{team1}{separator}{team2}'

    # Trim and remove extra spaces
    name = ' '.join(name.split())
    return name

async def fetch_and_process_url(browser, url, scroll_downs=1, sleep_duration=0.5, retry_count=3):
    for attempt in range(retry_count):
        try:
            page = await browser.newPage()
            await page.goto(url, {'waitUntil': 'networkidle0'})  # Consider waiting until the network is idle
            for _ in range(scroll_downs):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(sleep_duration)
            content = await page.content()
            await page.close()  # Ensure the page is closed even if an exception occurs
            return content
        except pyppeteer_errors.NetworkError as e:
            print(f"Attempt {attempt + 1} of {retry_count} failed: {str(e)}")
            await page.close()  # Ensure the page is closed in case of an exception
            if attempt == retry_count - 1:
                raise  # Re-raise the last exception if all retries fail

async def save_content_to_file(file_path, content, mode='w'):
    async with aiofiles.open(file_path, mode, encoding='utf-8') as file:
        await file.write(content)

async def extract_and_save_links(html_content, base_url, file_path, excluded_words, segment_condition=(2, 1)):
    max_segments, min_segments = segment_condition
    soup = BeautifulSoup(html_content, 'html5lib')
    links = soup.find_all('a', href=lambda x: x and x.startswith("line/"))
    unique_links = set()
    for link in links:
        full_url = base_url + link['href']
        if full_url == base_url + 'line/':
            continue
        if not any(word in full_url for word in excluded_words):
            num_segments = len(full_url.split('/')) - 3  # Adjust the offset based on the actual URL structure
            if max_segments >= num_segments >= min_segments:
                unique_links.add(full_url)
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
        for unique_link in unique_links:
            await file.write(unique_link + '\n')

async def extract_new_unique_links(processed_file_path, base_url, excluded_words, original_links):
    new_unique_links = set()
    try:
        async with aiofiles.open(processed_file_path, 'r', encoding='utf-8') as file:
            html_content = await file.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        page_links = soup.find_all('a', href=lambda x: x and x.startswith(""))
        for page_link in page_links:
            href_segments = page_link['href'].split('/')
            if href_segments[-1]:
                href_segments = href_segments[:-1]
            full_url = base_url + '/'.join(href_segments)
            num_segments = len(full_url.split('/')) - 3  # Adjust based on your URL structure
            if not any(word in full_url for word in excluded_words) and num_segments > 2:
                new_unique_links.add(full_url)
    except Exception as e:
        print(f"Error extracting new unique links: {e}")
    return list(new_unique_links)

async def read_html_file(file_path):
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        content = await file.read()
    return content

async def process_links(browser, file_path, output_file, base_url, excluded_words):
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        links = [line.strip() for line in await file.readlines()]
    for link in links:
        content = await fetch_and_process_url(browser, link, random.randint(3, 6), random.uniform(0.25, 0.75))
        await save_content_to_file(output_file, content + '\n\n', 'a')
    return links  # Return the original links for comparison

async def process_link(browser, url, output_file, semaphore):
    async with semaphore:
        content = await fetch_and_process_url(browser, url, random.randint(3, 6), random.uniform(0.25, 0.75))
        await save_content_to_file(output_file, content + '\n\n', 'a')

async def process_final_links(browser, file_path, output_file):
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        links = [line.strip() for line in await file.readlines()]

    # Create a semaphore with a limit of 10 concurrent tasks
    semaphore = asyncio.Semaphore(10)

    # Create tasks with semaphore passed to each
    tasks = [process_link(browser, link, output_file, semaphore) for link in links]

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

async def main():
    start_time = time.time()
    browser = await launch()  # Launch browser once at the start
    
    url = 'https://1xbet.es'
    base_url = 'https://1xbet.es/'
    excluded_words = ['bonus', 'rules', 'information', 'cookies', 'juegoseguro', 'app', 'jugarbien', 'authorizedgame', 'privacy', 'policy', 'ordenacionjuego', 'user', 'password']

    with open(ROOT_DIR / '1xbet/1xbet_links.html', 'w', encoding='utf-8') as file:
        file.write('')
    with open(ROOT_DIR / '1xbet/1xbet.html', 'w', encoding='utf-8') as file:
        file.write('')

    html_content = await fetch_and_process_url(browser, url, random.randint(3, 6), random.uniform(0.25, 0.75))
    await save_content_to_file(ROOT_DIR / '1xbet/1xbet.html', html_content)
    
    # Extract and save initial links with condition 2 > num_segments >= 1
    await extract_and_save_links(html_content, base_url, ROOT_DIR / '1xbet/1xbet_links.txt', excluded_words, segment_condition=(2, 1))
    
    # Process each link and append content
    original_links = await process_links(browser, ROOT_DIR / '1xbet/1xbet_links.txt', ROOT_DIR / '1xbet/1xbet_links.html', base_url, excluded_words)
    
    # Extract new unique links with condition 10 > num_segments >= 3
    new_unique_links = await extract_new_unique_links(ROOT_DIR / '1xbet/1xbet_links.html', base_url, excluded_words, set(original_links))
    
        # Save new unique links to '1xbet_v2.txt' with condition 10 > num_segments >= 3
    await save_content_to_file(ROOT_DIR / '1xbet/1xbet_links_v2.txt', '\n'.join(new_unique_links), 'w')

    # Process final links and append content to '1xbet.html'
    await process_final_links(browser, ROOT_DIR / '1xbet/1xbet_links_v2.txt', ROOT_DIR / '1xbet/1xbet.html')
    
    await browser.close()  # Close browser after all operations are done

    ruta_archivo = ROOT_DIR / '1xbet/1xbet.html'
    archivo_resultados = ROOT_DIR / '1xbet/1xbet.txt'

    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        html_content = archivo.read()

    soup = BeautifulSoup(html_content, 'html5lib')
    base_url = 'https://www.1xbet.es'

    processed_events = set()

    with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        events = soup.find_all(class_='c-events__item c-events__item--col')

        for event in events:
            teams = event.find_all(class_='c-events__team')
            if len(teams) >= 2:
                team_names = [clean_name(team.get_text(strip=True)) for team in teams]
                event_id = " vs ".join(team_names)
                
                if event_id in processed_events:
                    continue  # Skip duplicated event
                processed_events.add(event_id)
                
                all_odds = event.find_all(class_='c-bets__bet')
                odds_values = [odd.get_text(strip=True) for odd in all_odds if 'c-bets__bet--coef' in odd['class']]
                odds_to_include = 3 if len(odds_values) >= 4 else 2
                odds_values = odds_values[:odds_to_include]
                
                # Extract the event URL
                link_tag = event.find('a', class_='c-events__name')
                event_url = base_url + '/'+ link_tag['href'] if link_tag and 'href' in link_tag.attrs else 'URL not found'

                archivo_salida.write(f"{team_names[0]} - {team_names[1]}\n")
                for i, odd in enumerate(odds_values, start=1):
                    archivo_salida.write(f"  {i}: {odd}\n")
                archivo_salida.write(f"link -> {event_url}\n")
                archivo_salida.write("-----\n")
            else:
                print("Team names not found for an event.")

    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = elapsed_time / 60
    print(f"Script executed in {elapsed_time:.2f} seconds.")
    print(f"Script executed in {minutes:.2f} minutes.")

asyncio.run(main())