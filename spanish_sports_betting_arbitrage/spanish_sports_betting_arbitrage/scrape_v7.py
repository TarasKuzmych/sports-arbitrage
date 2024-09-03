from pyppeteer import launch, errors as pyppeteer_errors
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pool, cpu_count
from nltk.tokenize import word_tokenize
from collections import defaultdict
from phonetics import metaphone
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from math import ceil
import unicodedata
import requests
import aiofiles
import sqlite3
import asyncio
import aiohttp
import random
import httpx
import time
import json
import nltk
import re
import os
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

# Constants for the script
DATABASE_PATH = ROOT_DIR / 'odds.db'
AMOUNT_TO_BET = 100  # Fixed betting amount
MIN_ODDS = 1
MAX_ODDS = 10000
MIN_BETS = 2
MAX_BETS = 12
N_PROCESSES = cpu_count()  # Number of processes to us

# Download required NLTK resources
nltk.download('punkt')

# Adjust the threshold based on your specific needs
SIMILARITY_THRESHOLD = 77

async def fetch(session, url, cookies):
    async with session.get(url, cookies=cookies) as response:
        return await response.text()

# Shared utility functions
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


async def scrape_1xbet_async():
    async def fetch_and_process_url(browser, url, scroll_downs=1, sleep_duration=0.5, retry_count=3):
        for attempt in range(retry_count):
            try:
                page = await browser.newPage()
                await page.goto(url, {'waitUntil': 'networkidle0'}) 
                for _ in range(scroll_downs):
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(sleep_duration)
                content = await page.content()
                await page.close()
                return content
            except pyppeteer_errors.NetworkError as e:
                print(f"Attempt {attempt + 1} of {retry_count} failed: {str(e)}")
                await page.close() 
                if attempt == retry_count - 1:
                    raise 

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
                num_segments = len(full_url.split('/')) - 3 
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
                num_segments = len(full_url.split('/')) - 3 
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
        return links 
    
    async def process_link(browser, url, output_file, semaphore):
        async with semaphore:
            content = await fetch_and_process_url(browser, url, random.randint(3, 6), random.uniform(0.25, 0.75))
            await save_content_to_file(output_file, content + '\n\n', 'a')

    async def process_final_links(browser, file_path, output_file):
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            links = [line.strip() for line in await file.readlines()]
        semaphore = asyncio.Semaphore(10)
        tasks = [process_link(browser, link, output_file, semaphore) for link in links]
        await asyncio.gather(*tasks)

    async def main():
        start_time = time.time()
        browser = await launch() 
        
        url = 'https://1xbet.es/line'
        base_url = 'https://1xbet.es/'
        excluded_words = ['bonus', 'rules', 'information', 'cookies', 'juegoseguro', 'app', 'jugarbien', 'authorizedgame', 'privacy', 'policy', 'ordenacionjuego', 'user', 'password']

        with open(ROOT_DIR / '1xbet/1xbet_links.html', 'w', encoding='utf-8') as file:
            file.write('')
        with open(ROOT_DIR / '1xbet/1xbet.html', 'w', encoding='utf-8') as file:
            file.write('')

        html_content = await fetch_and_process_url(browser, url, random.randint(3, 6), random.uniform(0.25, 0.75))
        await save_content_to_file(ROOT_DIR / '1xbet/1xbet.html', html_content)
        await extract_and_save_links(html_content, base_url, ROOT_DIR / '1xbet/1xbet_links.txt', excluded_words, segment_condition=(2, 1))
        original_links = await process_links(browser, ROOT_DIR / '1xbet/1xbet_links.txt', ROOT_DIR / '1xbet/1xbet_links.html', base_url, excluded_words)
        new_unique_links = await extract_new_unique_links(ROOT_DIR / '1xbet/1xbet_links.html', base_url, excluded_words, set(original_links))
        await save_content_to_file(ROOT_DIR / '1xbet/1xbet_links_v2.txt', '\n'.join(new_unique_links), 'w')
        await process_final_links(browser, ROOT_DIR / '1xbet/1xbet_links_v2.txt', ROOT_DIR / '1xbet/1xbet.html')
        
        await browser.close() 

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
                        continue 
                    processed_events.add(event_id)
                    
                    all_odds = event.find_all(class_='c-bets__bet')
                    odds_values = [odd.get_text(strip=True) for odd in all_odds if 'c-bets__bet--coef' in odd['class']]
                    odds_to_include = 3 if len(odds_values) >= 4 else 2
                    odds_values = odds_values[:odds_to_include]
                    
                    link_tag = event.find('a', class_='c-events__name')
                    event_url = base_url + '/'+ link_tag['href'] if link_tag and 'href' in link_tag.attrs else 'URL not found'

                    archivo_salida.write(f"{team_names[0]} - {team_names[1]}\n")
                    for i, odd in enumerate(odds_values, start=1):
                        archivo_salida.write(f"  {i}: {odd}\n")
                    archivo_salida.write(f"link -> {event_url}\n")
                    archivo_salida.write("-----\n")
                else:
                    print("Team names not found for an event.")
    print('1xbet')


def scrape_aupabet():
    url = 'https://www.aupabet.es'

    cookies = {
        
        }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        archivo_resultados = ROOT_DIR / 'aupabet/aupabet.txt'
        with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
            top_apostado_block = soup.find("div", id="bloqueApuestasDestacadas")
            if top_apostado_block:
                for nombre in top_apostado_block.find_all("div", class_="infoEve"):
                    nombres = {}
                    partido_span = nombre.find("span", class_="partido")
                    if partido_span:
                        equipos = re.sub(r' vs\. ', ' - ', partido_span.get_text(strip=True))
                        equipos = re.sub(r'\(\+ \d+\)', '', equipos).strip()
                        # Apply clean_name function
                        nombres['teams'] = clean_name(equipos)

                    cuotas_ul = nombre.find_next("ul", class_=lambda x: x and x.startswith('it_'))
                    if cuotas_ul:
                        nombres['odds'] = []
                        counter = 1
                        for li in cuotas_ul.find_all("li"):
                            cuota = li.find("span", class_="coef").get_text(strip=True)
                            cuota = cuota.replace(',', '.')
                            nombres['odds'].append(f"{counter}: {cuota}")
                            counter += 1

                    archivo_salida.write(f"{nombres.get('teams', 'N/A')}\n")
                    for odd in nombres.get('odds', []):
                        archivo_salida.write(f"  {odd}\n")
                    archivo_salida.write("-----\n")

        with open(ROOT_DIR / 'aupabet/aupabet.html', 'w', encoding='utf-8') as file:
            file.write(response.text)

    else:
        print(f'Error while making the request. Response code: {response.status_code}')

async def scrape_777_async():
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
        try:
            async with aiofiles.open(file_path, mode, encoding='utf-8') as file:
                await file.write(content)
        except IOError as e:  # IOError includes FileNotFoundError, PermissionError, etc.
            print(f"Failed to save content to {file_path}: {e}")

    async def extract_and_save_links(html_content, base_url, file_path, excluded_words, segment_condition=(2, 1)):
        try:
            max_segments, min_segments = segment_condition
            soup = BeautifulSoup(html_content, 'html5lib')
            links = soup.find_all('a', href=lambda x: x and x.startswith("/"))
            unique_links = set()
            for link in links:
                full_url = base_url + link['href']
                if not any(word in full_url for word in excluded_words):
                    num_segments = len(full_url.split('/')) - 4  # Adjust the offset based on the actual URL structure
                    if max_segments > num_segments >= min_segments:
                        unique_links.add(full_url)
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                for unique_link in unique_links:
                    await file.write(unique_link + '\n')
        except Exception as e:
            print(f"Error during link extraction: {e}")

    async def extract_new_unique_links(processed_file_path, base_url, excluded_words, original_links):
        new_unique_links = set()
        try:
            async with aiofiles.open(processed_file_path, 'r', encoding='utf-8') as file:
                html_content = await file.read()
            soup = BeautifulSoup(html_content, 'html5lib')
            page_links = soup.find_all('a', href=lambda x: x and x.startswith("/"))
            for page_link in page_links:
                full_url = base_url + page_link['href']
                num_segments = len(full_url.split('/')) - 4  # Adjust based on your URL structure
                if not any(word in full_url for word in excluded_words) and 2 <= num_segments < 10:
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
            try:
                content = await fetch_and_process_url(browser, link, random.randint(3, 6), random.uniform(0.25, 0.75))
                await save_content_to_file(output_file, content + '\n\n', 'a')
            except Exception as e:
                print(f"Error processing link {link}: {e}")
        return links  # Return the original links for comparison

    async def process_link(browser, url, output_file, semaphore):
        async with semaphore:
            content = await fetch_and_process_url(browser, url, random.randint(3, 6), random.uniform(0.25, 0.75))
            await save_content_to_file(output_file, content + '\n\n', 'a')

    async def process_final_links(browser, file_path, output_file):
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            links = [line.strip() for line in await file.readlines()]

        # Create a semaphore with a limit of 10 concurrent tasks
        semaphore = asyncio.Semaphore(8)

        # Create tasks with semaphore passed to each
        tasks = [process_link(browser, link, output_file, semaphore) for link in links]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)
        
    # Main process starts here
    browser = await launch()  # Launch browser once at the start
    url = 'https://www.bet777.es'
    base_url = 'https://www.bet777.es'
    excluded_words = ['bola-de-piso','directo', 'ayuda', 'search', '_nuxt', 'promociones', 'resultados', 'match', 'outrights', 'event', 'resultado']

    html_content = await fetch_and_process_url(browser, url, random.randint(3, 6), random.uniform(0.25, 0.75))
    await save_content_to_file(ROOT_DIR / '777/777.html', html_content)

    await extract_and_save_links(html_content, base_url, ROOT_DIR / '777/777_links.txt', excluded_words, segment_condition=(2, 1))
    original_links = await process_links(browser, ROOT_DIR / '777/777_links.txt', ROOT_DIR / '777/777_links.html', base_url, excluded_words)
    new_unique_links = await extract_new_unique_links(ROOT_DIR / '777/777_links.html', base_url, excluded_words, set(original_links))
    await save_content_to_file(ROOT_DIR / '777/777_links_v2.txt', '\n'.join(new_unique_links), 'w')
    await process_final_links(browser, ROOT_DIR / '777/777_links_v2.txt', ROOT_DIR / '777/777.html')
    
    await browser.close()  # Close browser after all operations are done

    ruta_archivo = ROOT_DIR / '777/777.html'
    archivo_resultados = ROOT_DIR / '777/777.txt'

    async with aiofiles.open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        html_content = await archivo.read()

    soup = BeautifulSoup(html_content, 'html5lib')

    seen_events = set()
    base_url = 'https://www.bet777.es'

    async with aiofiles.open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        events = soup.find_all('div', class_='flex flex-row')
        
        for event in events:
            # Skip LIVE events
            if event.find('span', string="LIVE"):
                continue  # This skips the rest of the loop for live events
            
            teams = event.find_all('span', class_=['pr-1', 'font-medium'])  # IF STOPS WORKING ADD 'text-sm', 'truncate',
            if teams:
                team_names = ' - '.join([team.get_text(strip=True) for team in teams])
                title = clean_name(team_names)  
                
                if title not in seen_events:
                    seen_events.add(title)
                    
                odds = event.find_all('strong', class_='text-primary-500')
                odds_values = [odd.get_text(strip=True) for odd in odds]  # Define odds_values here
                
                if odds_values and len(odds_values) > 1:  # Check if odds_values is not empty
                    await archivo_salida.write(f"{title}\n")
                    for i, odd in enumerate(odds_values, start=1):
                        await archivo_salida.write(f"  {i}: {odd}\n")
                    # Extract event link
                    event_link_tag = event.find('a', href=True)
                    if event_link_tag:
                        event_link = event_link_tag['href']
                        full_link = f"{base_url}{event_link}"
                        await archivo_salida.write(f"link -> {full_link}\n")
                    await archivo_salida.write("-----\n")
    print('777')


async def scrape_bwin_async():
    async def fetch_and_process_url(browser, url, scroll_downs=1, sleep_duration=0.5, retry_count=3):
        page = None  # Initialize page as None
        for attempt in range(retry_count):
            try:
                page = await browser.newPage()
                await page.goto(url, {'waitUntil': 'networkidle0'})
                for _ in range(scroll_downs):
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(sleep_duration)
                content = await page.content()
                await page.close()
                return content
            except Exception as e:  # Broadening the catch to handle any exception
                print(f"Attempt {attempt + 1} of {retry_count} failed: {str(e)}")
                if page:  # Check if page has been initialized
                    await page.close()
                if attempt == retry_count - 1:
                    raise  # Re-raise the last exception if all retries fail

    async def save_content_to_file(file_path, content, mode='w'):
        try:
            async with aiofiles.open(file_path, mode, encoding='utf-8') as file:
                await file.write(content)
        except IOError as e:  # IOError includes FileNotFoundError, PermissionError, etc.
            print(f"Failed to save content to {file_path}: {e}")

    async def extract_and_save_links(html_content, base_url, file_path, excluded_words, segment_condition=(5, 2)):
        try:
            max_segments, min_segments = segment_condition
            soup = BeautifulSoup(html_content, 'html5lib')
            links = soup.find_all('a', href=lambda x: x and x.startswith("/es/sports/"))
            unique_links = set()
            for link in links:
                full_url = base_url + link['href']
                if not any(word in full_url for word in excluded_words):
                    num_segments = len(full_url.split('/')) - 4  # Adjust the offset based on the actual URL structure
                    if max_segments > num_segments >= min_segments:
                        unique_links.add(full_url + '/apuestas')
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                for unique_link in unique_links:
                    await file.write(unique_link + '\n')
        except Exception as e:
            print(f"Error during link extraction: {e}")

    async def extract_new_unique_links(processed_file_path, base_url, excluded_words, original_links):
        new_unique_links = set()
        try:
            async with aiofiles.open(processed_file_path, 'r', encoding='utf-8') as file:
                html_content = await file.read()
            soup = BeautifulSoup(html_content, 'html5lib')
            page_links = soup.find_all('a', href=lambda x: x and x.startswith("/es/sports/"))
            for page_link in page_links:
                full_url = base_url + page_link['href']
                num_segments = len(full_url.split('/')) - 4  # Adjust based on your URL structure
                if not any(word in full_url for word in excluded_words) and 3 <= num_segments < 5:
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
            try:
                content = await fetch_and_process_url(browser, link, random.randint(3, 6), random.uniform(0.25, 0.75))
                await save_content_to_file(output_file, content + '\n\n', 'a')
            except Exception as e:
                print(f"Error processing link {link}: {e}")
        return links  # Return the original links for comparison

    async def process_link(browser, url, output_file, semaphore):
        async with semaphore:
            content = await fetch_and_process_url(browser, url, random.randint(3, 6), random.uniform(0.25, 0.75))
            await save_content_to_file(output_file, content + '\n\n', 'a')

    async def process_final_links(browser, file_path, output_file):
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            links = [line.strip() for line in await file.readlines()]

        # Create a semaphore with a limit of 10 concurrent tasks
        semaphore = asyncio.Semaphore(4)

        # Create tasks with semaphore passed to each
        tasks = [process_link(browser, link, output_file, semaphore) for link in links]

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

    # Main process starts here
    browser = await launch()  # Launch browser once at the start
    url = 'https://sports.bwin.es/es/sports?popup=sports'
    base_url = 'https://sports.bwin.es'
    excluded_words = ['mañana', 'cupones', 'directo', 'páginadeequipo', 'eventos', 'hoy', 'todas', 'bandy', 'los-']
    
    html_content = await fetch_and_process_url(browser, url, random.randint(1, 6), random.uniform(0.5, 2.0))
    await save_content_to_file(ROOT_DIR / 'bwin/bwin.html', html_content)

    await extract_and_save_links(html_content, base_url, ROOT_DIR / 'bwin/bwin_links.txt', excluded_words, segment_condition=(5, 2))
    original_links = await process_links(browser, ROOT_DIR / 'bwin/bwin_links.txt', ROOT_DIR / 'bwin/bwin_links.html', base_url, excluded_words)
    new_unique_links = await extract_new_unique_links(ROOT_DIR / 'bwin/bwin_links.html', base_url, excluded_words, set(original_links))
    await save_content_to_file(ROOT_DIR / 'bwin/bwin_links_v2.txt', '\n'.join(new_unique_links), 'w')
    await process_final_links(browser, ROOT_DIR / 'bwin/bwin_links_v2.txt', ROOT_DIR / 'bwin/bwin.html')

    await browser.close()  # Close browser after all operations are done
    
    ruta_archivo = ROOT_DIR / 'bwin/bwin.html'
    archivo_resultados = ROOT_DIR / 'bwin/bwin.txt'

    # Create a set to store processed event names
    processed_events = {}

    async with aiofiles.open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        html_content = await archivo.read()

    soup = BeautifulSoup(html_content, 'html5lib')

    async with aiofiles.open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        event_blocks = soup.find_all(class_="grid-event")
        base_url = 'https://sports.bwin.es'
        
        for event_block in event_blocks:
            # Extract participant names to form the event title
            participant_elements = event_block.find_all(class_="participant")
            participants = [participant.get_text().strip() for participant in participant_elements]
            event_name = ' - '.join(participants)

            # Clean the event title
            title = clean_name(event_name) if event_name else None

            # Skip processing if no title or if the event name already exists in processed_events
            if not title or title in processed_events:
                continue

            option_groups = event_block.find_all('ms-option-group', class_="grid-option-group")
            
            # Retain original filtering for two-column ng-star-inserted
            specific_option_groups = [group for group in option_groups if "two-column ng-star-inserted" in " ".join(group.get("class", []))]

            # Apply new filtering criteria within the existing logic
            enhanced_option_groups = []
            for group in option_groups:
                if "grid-option-group grid-group ng-star-inserted" in " ".join(group.get("class", [])):
                    ms_options = group.find_all('ms-option', class_="grid-option ng-star-inserted", recursive=False)
                    if ms_options and all('ms-event-pick' in str(option) for option in ms_options):
                        enhanced_option_groups.append(group)

            # Determine which option groups to process, integrating both criteria
            if len(specific_option_groups) == 2:
                option_groups_to_process = [specific_option_groups[1]]
            elif enhanced_option_groups:
                option_groups_to_process = enhanced_option_groups
            else:
                option_groups_to_process = [group for group in option_groups if not group.find(class_="option-group-attribute")]

            all_odds = []

            for option_group in option_groups_to_process:
                odds_elements = option_group.find_all(class_="option-value")
                odds = [odds_element.get_text().strip() for odds_element in odds_elements]

                # Collect odds if available and break after the first set
                if odds:
                    all_odds.extend(odds)
                    break  # Stop after collecting the first set of odds

            # Find the link of the event
            link_element = event_block.find('a', class_="grid-info-wrapper fixed")
            event_link = base_url + link_element.get('href') if link_element else None

            # Skip the event if it contains only one odd or if there are no odds
            if len(all_odds) > 1:
                processed_events[title] = {
                    'event_block': event_block,
                    'odds': all_odds,
                    'link': event_link  # Store the link in the processed_events dict
                }

        for title, event_info in processed_events.items():
            if title and event_info['odds']:
                await archivo_salida.write(f"{title}\n")
                for i, odd in enumerate(event_info['odds'], start=1):
                    await archivo_salida.write(f"  {i}: {odd}\n")
                if event_info['link']:  # Check if the link is available and write it to the file
                    await archivo_salida.write(f"link -> {event_info['link']}\n")
                await archivo_salida.write(f"-----\n")
    print('Bwin')


async def scrape_betfair_async():
    # Load URLs from the original file
    async with aiofiles.open(ROOT_DIR / 'betfair/betfair_links.txt', mode='r') as url_file:
        urls = await url_file.read()
    urls = urls.splitlines()

    cookies = {
        
        }

    hrefs = []
    archivo_salida = ROOT_DIR / 'betfair/betfair_links.html'

    async with aiohttp.ClientSession(cookies=cookies) as session:
        for url in urls:
            # Add a random delay between requests
            delay = random.uniform(1.87, 2.77) # 1.86, 2.77
            await asyncio.sleep(delay)

            async with session.get(url, max_redirects=10, cookies=cookies) as response:
                if response.status == 200:
                    text = await response.text()

                    # Save the HTML content to a file
                    async with aiofiles.open(archivo_salida, mode='w', encoding='utf-8') as html_file:
                        await html_file.write(text)
                        soup = BeautifulSoup(text, 'html.parser')
                        # Find the script tag containing 'platformConfig'
                        script_tag = soup.find('script', string=re.compile(r'^\s*platformConfig', re.M))
                        if script_tag:
                            # Extract the JSON-like string
                            json_str = re.search(r'platformConfig = ({.*?});', script_tag.text, re.DOTALL).group(1)

                            # Parse the JSON string
                            platform_config = json.loads(json_str)

                            # Extract sport name from the URL
                            match = re.search(r'/sport/([^/?]+)', url)
                            if match:
                                sport_name = match.group(1)

                                # Extract HTML snippets from the config
                                for instruction in platform_config.get("page", {}).get("config", {}).get("instructions", []):
                                    if "html" in instruction.get("arguments", {}):
                                        snippet = instruction["arguments"]["html"]
                                        snippet_soup = BeautifulSoup(snippet, 'html.parser')
                                        for a_tag in snippet_soup.find_all('a', href=re.compile(f'^/sport/{sport_name}/')):
                                            href = a_tag['href']
                                            hrefs.append(href)
                        else:
                            print(f'Error: Response code {response.status}')

    # Write the hrefs to 'betfair_links_v2.txt'
    async with aiofiles.open(ROOT_DIR / 'betfair/betfair_links_v2.txt', mode='w') as file:
        for href in hrefs:
            await file.write('https://www.betfair.es' + href + '\n')

    # File to store the combined HTML content
    output_file_v2 = ROOT_DIR / 'betfair/betfair.html'

    async with aiofiles.open(output_file_v2, mode='w', encoding='utf-8') as html_file_v2:
        pass

    async with aiohttp.ClientSession(cookies=cookies) as session:
        for new_url in hrefs:
            # Random delay between requests
            delay = random.uniform(1.82, 2.87) # 1.87, 2.82
            await asyncio.sleep(delay)

            async with session.get(f'https://www.betfair.es{new_url}', max_redirects=10, cookies=cookies) as response:
                if response.status == 200:
                    text = await response.text()
                    async with aiofiles.open(output_file_v2, mode='a', encoding='utf-8') as html_file_v2:
                        await html_file_v2.write(text + '\n')
                else:
                    print(f'Error in request to {new_url}. Response code: {response.status}')

    ruta_archivo = ROOT_DIR / 'betfair/betfair.html'
    archivo_resultados = ROOT_DIR / 'betfair/betfair.txt'

    async with aiofiles.open(ruta_archivo, mode='r', encoding='utf-8') as archivo:
        html_content = await archivo.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    events = []
    processed_events = set()

    base_url = "https://www.betfair.es"

    # Loop through each event
    for event_info in soup.find_all("div", class_="event-information"):
        if 'ui-inplay' in event_info['class']:
            continue

        is_ice_hockey = any("ICE_HOCKEY" in a.get('data-sport', '') for a in event_info.find_all(True))

        event = {"teams": [], "odds": [], "link": ""}

        event_name_info = event_info.find("div", class_="event-name-info")
        if event_name_info:
            teams = event_name_info.find_all("span", class_=("team-name"))
            event_title = ' - '.join([team.get_text(strip=True) for team in teams])
            cleaned_event_title = clean_name(event_title)
            event["teams"] = cleaned_event_title.split(' - ')

        runner_lists = event_info.find_all("ul", class_="runner-list-selections")
        if runner_lists:
            last_runner_list = runner_lists[-1]
            selections = last_runner_list.find_all("li", class_="selection")

            if is_ice_hockey and len(selections) != 3:
                continue

            for selection in selections:
                outcome = selection.find("span", class_="ui-runner-price")
                if outcome:
                    event["odds"].append(outcome.get_text(strip=True))

        event_link = event_info.find("a", class_="ui-nav markets-number-arrow ui-top event-link ui-gtm-click")
        if event_link and 'href' in event_link.attrs:
            event["link"] = base_url + event_link['href']

        # Check if the odds are complete and valid
        if all(event["odds"]):
            event_id = " - ".join(event["teams"]) + " | " + " - ".join(event["odds"])
            if event_id not in processed_events:
                processed_events.add(event_id)
                events.append(event)

    async with aiofiles.open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        for e in events:
            await archivo_salida.write(" - ".join(e["teams"]) + "\n")
            for i, odd in enumerate(e["odds"], start=1):
                await archivo_salida.write(f"  {i}: {odd}\n")
            await archivo_salida.write(f"link -> {e['link']}\n")
            await archivo_salida.write("-" * 5 + "\n")
    print('Betfair')


async def scrape_dafabet_async():
    async def fetch_and_render(url, browser, retry_count=3):
        page = None
        for attempt in range(retry_count):
            try:
                page = await browser.newPage()
                await page.goto(url, {'waitUntil': 'networkidle0'})
                content = await page.content()
                return content
            except pyppeteer_errors.NetworkError as e:
                print(f"Attempt {attempt + 1} failed due to network error: {str(e)}")
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {str(e)}")
            finally:
                if page:
                    await page.close()
            if attempt == retry_count - 1:
                raise  # Reraise the last exception if all retries fail

    async def extract_links(html, base_url):
        try:
            soup = BeautifulSoup(html, 'html.parser')
            links = soup.find_all(href=lambda x: x and x.startswith("/es/sports/"))
            unique_links = set()

            for link in links:
                full_url = base_url + link['href']
                excluded_words = ['event', 'search', 'match', 'live', 'outrights', 'daily', 'odds', 'booster']
                if not any(word in full_url for word in excluded_words):
                    num_segments = len(full_url.split('/')) - 4  # Adjust as necessary
                    if 5 > num_segments >= 4:  # Adjust the condition as necessary
                        unique_links.add(full_url)
            return unique_links
        except Exception as e:
            print(f"Error extracting links: {e}")
            return set()  # Return an empty set on error

    async def write_links_to_file(links, file_path):
        try:
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                for link in links:
                    await file.write(link + '\n')
        except Exception as e:
            print(f"Error writing links to {file_path}: {e}")

    async def append_content_to_file(html, file_path):
        try:
            async with aiofiles.open(file_path, 'a', encoding='utf-8') as file:
                await file.write(html + '\n')
        except Exception as e:
            print(f"Error appending content to {file_path}: {e}")

    async def process_link(url, browser, final_html_file, semaphore):
        try:
            async with semaphore:
                content = await fetch_and_render(url, browser)
                await append_content_to_file(content, final_html_file)
        except Exception as e:
            print(f"Error processing link {url}: {e}")

    async def process_links(file_path, browser, final_html_file):
        semaphore = asyncio.Semaphore(5)
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                urls = [line.strip() for line in await file.readlines()]
            tasks = [process_link(url, browser, final_html_file, semaphore) for url in urls]
            await asyncio.gather(*tasks)
        except Exception as e:
            print(f"Error processing links from {file_path}: {e}")

    # Main process flow of scrape_dafabet_async    
    browser = await launch()  # Launch browser once at the start 
    url = 'https://www.dafabet.es/es/sports'
    base_url = 'https://www.dafabet.es'
    links_file = ROOT_DIR / 'dafabet/dafabet_links.txt'
    final_html_file = ROOT_DIR / 'dafabet/dafabet.html'

    # Initialize or clear the content of dafabet.html
    async with aiofiles.open(final_html_file, 'w', encoding='utf-8') as file:
        await file.write('')  # This empties the file or creates it if it doesn't exist
    
    try:
        content = await fetch_and_render(url, browser)
        links = await extract_links(content, base_url)
        await write_links_to_file(links, links_file)
        await process_links(links_file, browser, final_html_file)
    except Exception as e:
       print(f"An error occurred: {e}")
    finally:
        await browser.close()

    ruta_archivo = ROOT_DIR / 'dafabet/dafabet.html'
    archivo_resultados = ROOT_DIR / 'dafabet/dafabet.txt'

    # Create a set to store processed event names
    seen_titles = set()

    async with aiofiles.open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        html_content = await archivo.read()

    soup = BeautifulSoup(html_content, 'html5lib')
    base_url = 'https://www.dafabet.es'
    async with aiofiles.open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        # Find all event components
        for event_component in soup.find_all('div', class_='event-component'):
            # Check for live scores and skip if present
            if event_component.find('div', class_='live-scores'):
                continue  # Skip this event because it has live scores

            teams = event_component.find_all('a', class_='opponent-name')
            if len(teams) == 2:
                event_name = f"{teams[0].get_text(strip=True)} - {teams[1].get_text(strip=True)}"
                cleaned_event_name = clean_name(event_name)
            else:
                # Skip this event if it doesn't have exactly two teams
                continue
            
            # Check if the event has already been processed
            if cleaned_event_name in seen_titles:
                continue  # Skip this event
            seen_titles.add(cleaned_event_name)  # Add event name to the set
            
            # Extract odds
            odds = []
            for outcome_button in event_component.find_all('div', class_='outcome-button'):
                odd_value = outcome_button.find('span', class_='formatted_price')
                if odd_value:
                    odds_value_text = odd_value.get_text(strip=True)
                    if odds_value_text:  # Make sure the odd value is not empty
                        odds.append(odds_value_text)
            
            # Skip the event if it has less than two odds or if one of the odds is empty
            if len(odds) < 2:
                continue
            
            # Extract the event link
            event_link = event_component.find('a', class_='opponent-name')['href']
            full_event_link = base_url + event_link

            # Write to file asynchronously
            await archivo_salida.write(f'{cleaned_event_name}\n')
            for index, odd_value in enumerate(odds, start=1):
                await archivo_salida.write(f'  {index}: {odd_value}\n')
            await archivo_salida.write(f'link -> {full_event_link}\n')
            await archivo_salida.write('-----\n')
    print('Dafabet')



async def scrape_interwetten_async():
    url = 'https://www.interwetten.es'

    cookies = {
        
        }

    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, max_redirects=10, cookies=cookies) as response:
            if response.status == 200:
                text = await response.text()
                async with aiofiles.open(ROOT_DIR / 'interwetten/interwetten_links.html', 'w', encoding='utf-8') as file:
                    await file.write(text)

                soup = BeautifulSoup(text, 'html.parser')
                unique_hrefs = set()
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    if href.startswith('/es/apuestas-deportivas/l/') and 'especial' not in href and 'especiales' not in href:
                        unique_hrefs.add(f'{url}{href}')

                async with aiofiles.open(ROOT_DIR / 'interwetten/interwetten_links.txt', 'w', encoding='utf-8') as file:
                    for href in unique_hrefs:
                        await file.write(f'{href}\n')

                async with aiofiles.open(ROOT_DIR / 'interwetten/interwetten.html', 'w', encoding='utf-8') as file:
                    pass  # Clearing the contents

                # Read the links and fetch their content
                async with aiofiles.open(ROOT_DIR / 'interwetten/interwetten_links.txt', 'r', encoding='utf-8') as file:
                    links = await file.read()
                links = links.splitlines()

                for link in links:
                    try:
                        delay = random.uniform(1.57, 2.77) # 1.68 - 2.75
                        await asyncio.sleep(delay)
                        async with session.get(link, max_redirects=10, cookies=cookies) as response:
                            if response.status == 200:
                                text = await response.text()
                                async with aiofiles.open(ROOT_DIR / 'interwetten/interwetten.html', 'a', encoding='utf-8') as file:
                                    await file.write(text + "\n\n")
                            else:
                                print(f'Error accessing {link}: Status code {response.status}')
                    except Exception as e:
                        print(f'An error occurred while accessing {link}: {e}')

                # Post-processing of the HTML content
                archivo_resultados = ROOT_DIR / 'interwetten/interwetten.txt'
                async with aiofiles.open(ROOT_DIR / 'interwetten/interwetten.html', 'r', encoding='utf-8') as file:
                    html_content = await file.read()
                soup = BeautifulSoup(html_content, 'html.parser')

                async with aiofiles.open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
                    base_url = 'https://www.interwetten.es'
                    for event_row in soup.find_all('tr', class_=lambda x: x and x in ['odd', 'even']):
                        # Skip rows with 'Handicap' in any nested 'tr' element's 'data-betting' attribute
                        if any('Handicap' in nested_tr.get('data-betting', '') for nested_tr in event_row.find_all('tr', recursive=True)):
                            continue

                        participants = [p.get_text() for p in event_row.find_all('span', class_='tip-name', itemprop='name') if p.get_text() != "Empate"]
                        if not (2 <= len(participants) <= 3):
                            continue  # Skip if not the correct number of participants
                        
                        # Clean the participants' names
                        participants_clean = [participant.replace(',', '') for participant in participants]

                        # Construct event title
                        event_title = ' - '.join(participants_clean)
                        event = clean_name(event_title)  # Assuming `clean_name` is a function defined elsewhere

                        # Find the event link
                        event_link_element = event_row.find('a', class_='url', href=True)
                        event_link = base_url + event_link_element['href'] if event_link_element else "Link not found"

                        await archivo_salida.write(event+"\n")
                        counter = 1
                        for betting_offer in event_row.find_all('td', class_='BETTINGOFFER'):
                            odds = betting_offer.find('strong').text.strip().replace(',', '')
                            await archivo_salida.write(f"  {counter}: {odds}\n")
                            counter += 1
                        await archivo_salida.write(f"link -> {event_link}\n")
                        await archivo_salida.write("-----\n")

    print('Interwetten')

def scrape_kirolbet():
    url = 'https://apuestas.kirolbet.es/'

    cookies = {
        
        }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        html_content = response.text

        with open(ROOT_DIR / 'kirolbet/kirolbet.html', 'w', encoding='utf-8') as file:
            file.write(html_content)

        soup = BeautifulSoup(html_content, 'html.parser')

        archivo_resultados = ROOT_DIR / 'kirolbet/kirolbet.txt'

        with open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
            top_apostado_block = soup.find("div", id="bloqueApuestasDestacadas")
            if top_apostado_block:
                for nombre in top_apostado_block.find_all("div", class_="infoEve"):
                    nombres = {}
                    partido_span = nombre.find("span", class_="partido")
                    if partido_span:
                        equipos = re.sub(r' vs\. ', ' - ', partido_span.get_text(strip=True))
                        equipos = re.sub(r'\(\+ \d+\)', '', equipos).strip()
                        # Apply clean_name function
                        nombres['teams'] = clean_name(equipos)

                    cuotas_ul = nombre.find_next("ul", class_=lambda x: x and x.startswith('it_'))
                    if cuotas_ul:
                        nombres['odds'] = []
                        counter = 1
                        for li in cuotas_ul.find_all("li"):
                            cuota = li.find("span", class_="coef").get_text(strip=True)
                            cuota = cuota.replace(',', '.')
                            nombres['odds'].append(f"{counter}: {cuota}")
                            counter += 1

                    archivo_salida.write(f"{nombres.get('teams', 'N/A')}\n")
                    for odd in nombres.get('odds', []):
                        archivo_salida.write(f"  {odd}\n")
                    archivo_salida.write("-----\n")
    else:
        print(f'Error while making the request. Response code: {response.status_code}')


async def scrape_marca_async():
    url = 'https://deportes.marcaapuestas.es/es/apuestas-futbol'

    cookies = {
    
    }

    ruta_archivo = ROOT_DIR / 'marca/marca.html'
    archivo_resultados = ROOT_DIR / 'marca/marca.txt'

    # Ensure the file is empty before starting
    async with aiofiles.open(ruta_archivo, 'w', encoding='utf-8') as initial_file:
        await initial_file.write('')

    async with httpx.AsyncClient(cookies=cookies) as client:
        # Request the main page
        response = await client.get(url, follow_redirects=True)
        if response.status_code == 200:
            # Save the main page HTML
            async with aiofiles.open(ROOT_DIR / 'marca/marca.html', 'w', encoding='utf-8') as file:
                await file.write(response.text)

            # Parse the main page HTML to find links
            soup = BeautifulSoup(response.text, 'html.parser')
            expanders = soup.find_all('li', class_='expander')
            valid_expanders = [expander for expander in expanders if 'Apuestas a Largo Plazo' not in expander.text]

            links = []
            for expander in valid_expanders:
                for a in expander.find_all('a', href=True):
                    link = 'https://deportes.marcaapuestas.es' + a['href']
                    if all(substring not in link for substring in ['apuestas-', 'Ganador', 'Winner', 'Apuesta-a-largo-plazo', 'Alcanza-Final', 'Nombre-de-los-Finalistas']) and link not in links:
                        links.append(link)

            # Save the found links to a file
            async with aiofiles.open(ROOT_DIR / 'marca/marca_links.txt', 'w', encoding='utf-8') as file:
                for link in links:
                    await file.write(link + '\n')

            # For each link, request and append the HTML to the main HTML file
            for link in links:
                delay = random.uniform(1.87, 2.77)
                await asyncio.sleep(delay)
                try:
                    link_response = await client.get(link, follow_redirects=True)
                    if link_response.status_code == 200:
                        async with aiofiles.open(ROOT_DIR / 'marca/marca.html', 'a', encoding='utf-8') as file:
                            await file.write("\n<!-- Page Separator -->\n" + link_response.text)
                except Exception as e:
                    print(f'Exception for URL {link}: {e}')

        else:
            print(f'Error while making the request to {url}. Response code: {response.status_code}')

    # Once all HTML is saved, parse the combined HTML to extract and save odds and titles
    async with aiofiles.open(ROOT_DIR / 'marca/marca.html', 'r', encoding='utf-8') as file:
        combined_html = await file.read()
    
    soup = BeautifulSoup(combined_html, 'html.parser')
    seen_titles = set()

    async with aiofiles.open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        base_url = "https://deportes.marcaapuestas.es"
        eventos = soup.find_all('tr', class_='mkt')
        for evento in eventos:
            # Check if the event is live
            if evento.find('span', class_='will-be-inplay-image is-inplay'):
                continue  # Skip this event as it's a live event

            participantes = []
            cuotas_info = []
            sequence_number = 1

            cuotas = evento.find_all('td', class_='seln')
            for cuota in cuotas:
                draw_label_element = cuota.find('span', class_='seln-draw-label')
                if draw_label_element and draw_label_element.text.strip() == 'X':
                    cuota_valor_element = cuota.find('span', class_='price dec')
                    if cuota_valor_element:
                        cuota_valor = cuota_valor_element.text.strip()
                        cuotas_info.append(f"  {sequence_number}: {cuota_valor}")
                else:
                    nombre_evento_element = cuota.find('span', class_='seln-name')
                    if nombre_evento_element:
                        nombre_evento = nombre_evento_element.text.strip()
                        participantes.append(nombre_evento)

                        cuota_valor_element = cuota.find('span', class_='price dec')
                        if cuota_valor_element:
                            cuota_valor = cuota_valor_element.text.strip()
                            cuotas_info.append(f"  {sequence_number}: {cuota_valor}")

                sequence_number += 1  # Increment sequence number after processing each cuota

            # Construct and write the title above the odds
            if participantes:
                title = " - ".join([(p) for p in participantes])
                # Check if this event title has already been encountered
                if title not in seen_titles:
                    # Add the title to the set of seen titles
                    seen_titles.add(title)

                    # Attempt to find the event link
                    event_link_element = evento.find('a', href=True)
                    event_link = base_url + event_link_element['href'] if event_link_element else "Link not found"

                    # Write the event title and odds to the file
                    clean_title = clean_name(title)
                    await archivo_salida.write(f"{clean_title}\n")
                    for cuota in cuotas_info:
                        await archivo_salida.write(f"{cuota}\n")
                    await archivo_salida.write(f"link -> {event_link}\n")
                    await archivo_salida.write("-----\n")

        eventos = soup.find_all('tbody', class_='')
        for evento in eventos:
            rows = evento.find_all('tr')
            if len(rows) < 2:  # Ensure there are at least two rows for teams
                continue

            event_name_cell = rows[0].find('td', class_='event-name')
            if event_name_cell:
                anchor = event_name_cell.find('a')
                if anchor and 'href' in anchor.attrs:
                    href = anchor['href']
                    # Construct the full event link
                    event_link = base_url + href

                    # Splitting the href to extract team names
                    team_names = re.search(r'/([^/]+)-%40-([^/]+)$', href)
                    if team_names:
                        team1, team2 = team_names.groups()
                        team1 = team1.replace('-', ' ')
                        team2 = team2.replace('-', ' ')

                        # Fetching odds
                        cuotas_info = []
                        for i, row in enumerate(rows[:2]):
                            cuota_element = row.find('td', class_='mkt-sort mkt-sort-H2HT')
                            if cuota_element:
                                cuota_valor_element = cuota_element.find('span', class_='price dec')
                                if cuota_valor_element:
                                    cuota_valor = cuota_valor_element.text.strip()
                                    cuotas_info.append(f"  {i + 1}: {cuota_valor}")

                        # Only write to file if both teams have odds
                        if len(cuotas_info) == 2:
                            event_name = f"{team1} - {team2}"
                            event_name_clean = clean_name(event_name)
                            await archivo_salida.write(f"{event_name_clean}\n")
                            for cuota in cuotas_info:
                                await archivo_salida.write(f"{cuota}\n")
                            await archivo_salida.write(f"link -> {event_link}\n")
                            await archivo_salida.write("-----\n")
        else:
            print(f'Error while making the request to {url}. Response code: {response.status_code}')
    print('Marca')


async def scrape_marathonbet_async():
    def is_nba(event_path):
        return 'Basketball/NBA' in event_path

    def is_nhl(event_path):
        return 'Ice+Hockey/NHL' in event_path

    url = 'https://www.marathonbet.es/es/?cppcids=all'

    cookies = {
    
    }

    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, max_redirects=10, cookies=cookies) as response:
            if response.status == 200:
                text = await response.text()
                async with aiofiles.open(ROOT_DIR / 'marathonbet/marathonbet_links.html', 'w', encoding='utf-8') as file:
                    await file.write(text)
            else:
                print(f'Error while making the request. Response code: {response.status}')

            # Read the HTML file and parse it
            async with aiofiles.open(ROOT_DIR / 'marathonbet/marathonbet_links.html', 'r', encoding='utf-8') as file:
                content = await file.read()

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

            async with aiofiles.open(ROOT_DIR / 'marathonbet/marathonbet_links.txt', 'w', encoding='utf-8') as file:
                for link in links:
                    await file.write(link + '\n')

            async with aiofiles.open(ROOT_DIR / 'marathonbet/marathonbet.html', 'w', encoding='utf-8') as file:
                pass  # Clear file content

            async with aiofiles.open(ROOT_DIR / 'marathonbet/marathonbet_links.txt', 'r', encoding='utf-8') as file:
                links = await file.readlines()

            for link in links:
                link = link.strip()
                await asyncio.sleep(random.uniform(1.59, 2.82))  # Existing random delay 1.58 - 2.85

                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        async with session.get(link, max_redirects=10, cookies=cookies) as response:
                            if response.status == 200:
                                text = await response.text()
                                async with aiofiles.open(ROOT_DIR / 'marathonbet/marathonbet.html', 'a', encoding='utf-8') as file:
                                    await file.write(text + '\n')
                                break  # Exit the retry loop on successful response
                            else:
                                print(f'Error making the request to {link}. Response code: {response.status}')
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(1)  # Wait before retrying
                    except aiohttp.ClientError as e:
                        print(f'Marathonbet, attempt {attempt + 1}: Error making the request to {link}. Error: {e}')
                        if attempt < max_retries - 1:
                            await asyncio.sleep(1)  # Wait before retrying

        ruta_archivo = ROOT_DIR / 'marathonbet/marathonbet.html'
        archivo_resultados = ROOT_DIR / 'marathonbet/marathonbet.txt'

        # Set to track unique events
        unique_events = set()

        async with aiofiles.open(ruta_archivo, 'r', encoding='utf-8') as archivo:
            html_content = await archivo.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        async with aiofiles.open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
            nombres = soup.find_all('div', class_='bg coupon-row')
            
            # Base URL for constructing the event link
            base_url = 'https://www.marathonbet.es/es/betting/'

            # Set to track unique events
            unique_events = set()

            for nombre in nombres:
                event_path = nombre.get('data-event-path', '')
                event_link = base_url + event_path
                is_nba_event = is_nba(event_path)
                is_nhl_event = is_nhl(event_path)

                # Define and clean the event name
                nombre_name = nombre['data-event-name'].replace(' vs ', ' - ').replace(' @ ', ' - ')
                nombre_name = clean_name(nombre_name)

                # Check if event is unique
                if nombre_name not in unique_events:
                    unique_events.add(nombre_name)

                    cuotas = {}

                    # Find all 'td' elements with class 'price'
                    cuota_elements = nombre.find_all('td', class_='price')

                    for i, cuota in enumerate(cuota_elements, start=1):
                        market_type = cuota.get('data-market-type')
                        if market_type in ['RESULT', 'RESULT_2WAY']:
                            cuota_value = cuota.find('span', class_='selection-link').get_text()
                            cuotas[str(i)] = cuota_value

                    # Proceed only if cuotas are found
                    if cuotas:
                        # Swap the teams for NBA or NHL events
                        if is_nba_event or is_nhl_event:
                            nombre_name_parts = nombre_name.split(' - ')
                            if len(nombre_name_parts) == 2:
                                nombre_name = ' - '.join(nombre_name_parts[::-1])

                        # Swap odds for NBA events and NHL events, ensuring keys exist
                        if is_nba_event:
                            if '1' in cuotas and '2' in cuotas:
                                cuotas['1'], cuotas['2'] = cuotas['2'], cuotas['1']
                        elif is_nhl_event:
                            if '1' in cuotas and '3' in cuotas:
                                cuotas['1'], cuotas['3'] = cuotas['3'], cuotas['1']

                        await archivo_salida.write(f"{nombre_name}\n")
                        for key, value in cuotas.items():
                            await archivo_salida.write(f"  {key}: {value}\n")
                        # Write the event link
                        await archivo_salida.write(f"link -> {event_link}\n")
                        await archivo_salida.write("-----\n")
    print('Marathonbet')


async def scrape_pokerstars_async():
    url = 'https://www.pokerstars.es/sports/'

    cookies = {
        
        }

    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url, max_redirects=10, cookies=cookies) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')

                async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'w', encoding='utf-8') as file:
                    await file.write(text)

                links = soup.find_all(href=lambda x: x and x.startswith("/sports/"))

                excluded_links = [
                    "https://www.pokerstars.es/sports/my-bets/open/",
                    "https://www.pokerstars.es/sports/isp/games/rules/",
                    "https://www.pokerstars.es/sports/tennis/"
                ]

                # Words to exclude in the links
                excluded_words = ['jugadores', 'especiales', 'apuestas']

                unique_links = set()
                
                async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.txt', 'w', encoding='utf-8') as file:
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
                        await file.write(unique_link + '\n')
                        if '/sports/futbol/' in unique_link:
                            modified_link = unique_link + 'competitions/'
                            await file.write(modified_link + '\n')  # Write the modified link beneath the original
                        elif '/sports/carreras-de-caballos/' in unique_link:
                            modified_link = unique_link + 'meetings/'
                            await file.write(modified_link + '\n')

                async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'w', encoding='utf-8') as file:
                    await file.write('')

                async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.txt', 'w', encoding='utf-8') as file:
                    for unique_link in unique_links:
                        await file.write(unique_link + '\n')
                        if '/sports/futbol/' in unique_link:
                            modified_link = unique_link + 'competitions/'
                            await file.write(modified_link + '\n')  # Write the modified link beneath the original
                        elif '/sports/carreras-de-caballos/' in unique_link:
                            modified_link = unique_link + 'meetings/'
                            await file.write(modified_link + '\n')

                async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.txt', 'r', encoding='utf-8') as file:
                    links = await file.read()
                links = links.splitlines()

                for link in links:
                    await asyncio.sleep(random.uniform(1.57, 2.87)) # 1.57, 2.85
                    async with session.get(link, max_redirects=10, cookies=cookies) as link_response:
                        if link_response.status == 200:
                            link_text = await link_response.text()
                            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'a', encoding='utf-8') as html_file:
                                await html_file.write(link_text + '\n')
                        else:
                            print(f'Error while fetching {link}. Response code: {link_response.status}')

            # Clear the existing content in 'pokerstars_links.html'
            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'w', encoding='utf-8') as file:
                await file.write('')

            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.txt', 'r', encoding='utf-8') as file:
                contents = await file.read()  # Read the file contents asynchronously
                for url in contents.splitlines():  #
                    # Sleep for a random duration between requests
                    await asyncio.sleep(random.uniform(1.57, 2.87)) # 1.57, 2.85

                    # Send the request to the URL
                    response = requests.get(url.strip(), cookies=cookies)

                    # Check if the request was successful
                    async with session.get(url, max_redirects=10, cookies=cookies) as response:
                        if response.status == 200:
                            # Append the HTML content to 'pokerstars_links.html'
                            text_content = await response.text()
                            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'a', encoding='utf-8') as html_file:
                                await html_file.write(text_content + '\n')
                        else:
                            print(f'Error while fetching {url}. Response code: {response.status}')

            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.txt', 'r', encoding='utf-8') as file:
                file_content = await file.read()  # Await the coroutine and get the file content
                original_links = set(file_content.splitlines())
                
            # Initialize a set for new, unique links
            unique_links = set()

            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links.html', 'r', encoding='utf-8') as html_file:
                html_content = await html_file.read()  # Correctly call the read method and await its result
                soup = BeautifulSoup(html_content, 'html.parser')
                links = soup.find_all(href=lambda x: x and x.startswith("/sports/"))

                for link in links:
                    full_url = 'https://www.pokerstars.es' + link['href']
                    if ('in-play' in full_url or 
                        any(full_url.startswith(excluded_link) for excluded_link in excluded_links) or 
                        full_url in original_links or
                        any(word in full_url for word in excluded_words)):
                        continue

                    full_url = full_url.replace('/matches', '')
                    num_segments = len(full_url.split('/')) - 4

                    if 6 > num_segments >= 4:
                        if any(full_url.startswith(original_link) for original_link in original_links):
                            unique_links.add(full_url)
            
            # Write new unique links to 'pokerstars_links_v2.txt'
            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links_v2.txt', 'w', encoding='utf-8') as file:
                for unique_link in unique_links:
                    await file.write(unique_link + '\n')

            # Clear the existing content in 'pokerstars.html'
            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars.html', 'w', encoding='utf-8') as file:
                await file.write('')
            
            # Read URLs from 'pokerstars_links_v2.txt' and process each URL
            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars_links_v2.txt', 'r', encoding='utf-8') as file:
                contents = await file.read()  # Read the file contents asynchronously
                for url in contents.splitlines():
                    # Sleep for a random duration between requests
                    await asyncio.sleep(random.uniform(1.28, 1.86)) # 1.57, 2.85

                    # Send the request to the URL
                    async with session.get(url.strip(), max_redirects=10, cookies=cookies) as response:
                        if response.status == 200:
                            text_content = await response.text()  # Correctly await the text of the response
                            # Append the HTML content to 'pokerstars.html'
                            async with aiofiles.open(ROOT_DIR / 'pokerstars/pokerstars.html', 'a', encoding='utf-8') as html_file:
                                await html_file.write(text_content + '\n')
                        else:
                            print(f'Error while fetching {url}. Response code: {response.status}')

            lock = asyncio.Lock()

            async def process_data(pattern, html_content, archivo_salida, section):
                matches = pattern.finditer(html_content)
                processed_events = set()
                async with lock:  # Acquire the lock before opening the file
                    async with aiofiles.open(archivo_salida, 'w', encoding='utf-8') as file:
                        for match in matches:  # Iterate over each match object
                            json_string = match.group(1)
                            json_string = json_string.replace('u002F', '/') # erased .replace("'", '"') which may be needed as sometimes devs push updates. If starts playing definitely add the .replace
                            try:
                                data = json.loads(json_string)
                                if section in ['in_play', 'upcoming_events', 'competition_events', 'cms_banner']:
                                    competitions_data = data.get('competitions', {})
                                    event_types_data = data.get('eventTypes', {})
                                    events_data = data.get('events', {})
                                    markets_data = data.get('markets', {})
                                    for event_id, event_info in events_data.items():
                                        # Check if event is not in play
                                        if not event_info.get("isInPlay", False):  # This line filters out events that are in play 
                                            # Replace ' @ ' with ' - ' and clean the name
                                            event_name = event_info.get("eventName", "Unknown Event").replace(' @ ', ' - ').replace(' v ', ' - ')
                                            event_name = clean_name(event_name)

                                            market_info = None
                                            event_id_int = int(event_id) if event_id.isdigit() else None

                                            event_id_str = str(event_info.get('eventId'))
                                            competition_id = str(event_info.get('competitionId'))
                                            event_slug = event_info.get('eventSlug')
                                            event_type_id = str(event_info.get('eventTypeId'))

                                            # List of all markets for this event
                                            event_markets = [inner_dict for market_id, inner_dict in markets_data.items()
                                                            if isinstance(inner_dict, dict) and inner_dict.get('eventId') == event_id_int]

                                            if len(event_markets) > 1:
                                                # If multiple markets, filter for 'MONEY_LINE'
                                                for market in event_markets:
                                                    if market.get('marketType') == 'MONEY_LINE':
                                                        market_info = market
                                                        break
                                            elif event_markets:
                                                # If only one market or no 'MONEY_LINE' market in multiple, use the available market
                                                market_info = event_markets[0]

                                            competition_slug = competitions_data.get(competition_id, {}).get('competitionSlug')
                                            event_type_slug = event_types_data.get(event_type_id, {}).get('eventTypeSlug')

                                            # Construct the event URL
                                            if competition_slug and event_slug and event_type_slug:
                                                base_url = "https://www.pokerstars.es/sports/"
                                                event_url = f"{base_url}{event_type_slug}/{event_type_id}/{competition_slug}/{competition_id}/{event_slug}/{event_id_str}/"

                                            await file.write(f"{event_name}\n")
                                            if market_info:
                                                runners = market_info.get("runners", [])
                                                for idx, runner in enumerate(runners, 1):
                                                    name = runner.get("runnerName", "Unknown")
                                                    odds = runner.get("winRunnerOdds", {}).get("decimalDisplayOdds", {}).get("decimalOdds", "N/A")
                                                    await file.write(f"  {idx}: {odds}\n")
                                                # Addition to write the event URL
                                                await file.write(f"link -> {event_url}\n")
                                            await file.write("-----\n")

                                elif section == 'next_races':
                                    markets_data = data.get('markets', {})
                                    for market_id, market_info in markets_data.items():
                                        runners = market_info.get("runners", [])
                                        runners_names = []
                                        runners_odds = []
                                        incomplete_market = False

                                        for idx, runner in enumerate(runners, 1):
                                            name = runner.get("runnerName", "Unknown")
                                            if "favorito sin nombre" not in name.lower():
                                                odds = runner.get("winRunnerOdds", {}).get("decimalDisplayOdds", {}).get("decimalOdds", None)
                                                if odds is None:
                                                    incomplete_market = True
                                                    break
                                                runners_names.append(name)
                                                runners_odds.append(f"  {idx}: {odds}")

                                        event_identifier = f"{'-'.join(runners_names)}-{'-'.join(runners_odds)}"
                                        if not incomplete_market and runners_names and event_identifier not in processed_events:
                                            processed_events.add(event_identifier)
                                            await file.write(' - '.join(runners_names) + "\n")
                                            for runner_odds in runners_odds:
                                                await file.write(runner_odds + "\n")
                                            await file.write("-----\n")

                            except json.JSONDecodeError as e:
                                print(f"An error occurred while parsing JSON for {section}: {e}")
                        else:
                            print(f"No matching JSON found in the HTML file for {section}.")

            ruta_archivo = ROOT_DIR / 'pokerstars/pokerstars.html'
            archivo_resultados = ROOT_DIR / 'pokerstars/pokerstars.txt'

            async with aiofiles.open(ruta_archivo, 'r', encoding='utf-8') as archivo:
                html_content = await archivo.read()

            patterns = {
                'next_races': re.compile(
                    r"window\.__INITIAL_STATE__\['isp-sports-widget-next-races(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-next-races(?:/.+?)?'\] \|\| {},\s*(\{.*?\})\);",
                    re.DOTALL
                ),
                'in_play': re.compile(
                    r"window\.__INITIAL_STATE__\['isp-sports-widget-home-in-play(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-home-in-play(?:/.+?)?'\] \|\| {},\s*(\{.*?\})\);",
                    re.DOTALL
                ),
                'upcoming_events': re.compile(
                    r"window\.__INITIAL_STATE__\['isp-sports-widget-upcoming-events(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-upcoming-events(?:/.+?)?'\] \|\| {},\s*(\{.*?\})\);",
                    re.DOTALL
                ),
                'cms_banner' : re.compile(
                    r"window\.__INITIAL_STATE__\['isp-sports-widget-cms-banner(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-cms-banner(?:/.+?)?'\],\s*(\{.*?\})\);",
                    re.DOTALL
                ),
                'competition_events': re.compile(
                    r"window\.__INITIAL_STATE__\['isp-sports-widget-competition-events(?:/.+?)?'\]\s*=\s*Object\.assign\(window\.__INITIAL_STATE__\['isp-sports-widget-competition-events(?:/.+?)?'\] \|\| {},\s*(\{.*?\})\);",
                    re.DOTALL
                )
            }

            #await process_data(patterns['upcoming_events'], html_content, archivo_resultados, 'upcoming_events')
            #await process_data(patterns['next_races'], html_content, archivo_resultados, 'next_races')
            #await process_data(patterns['in_play'], html_content, archivo_resultados, 'in_play')
            await process_data(patterns['competition_events'], html_content, archivo_resultados, 'competition_events')
            #await process_data(patterns['cms_banner'], html_content, archivo_resultados, 'cms_banner')
    print('Pokerstars')


async def scrape_tonybet_async():
    async def fetch_and_process_url(url, scroll_downs=1, sleep_duration=0.5):
        browser = await launch()
        try:
            page = await browser.newPage()
            await page.goto(url, {'waitUntil': ['domcontentloaded', 'networkidle2']})
            for _ in range(scroll_downs):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(sleep_duration)
            content = await page.content()
        except pyppeteer_errors.TimeoutError as e:
            print(f"Timeout error occurred when navigating to {url}: {e}")
            content = 'THERE HAS BEEN A TIMEOUT'  # Handle as needed, perhaps with an empty string or a retry logic
        finally:
            await page.close()
            await browser.close()
        return content

    async def save_content_to_file(file_path, content, mode='w'):
        async with aiofiles.open(file_path, mode, encoding='utf-8') as file:
            await file.write(content)

    async def extract_new_unique_links(processed_file_path, base_url, excluded_words, original_links):
        new_unique_links = set()
        try:
            async with aiofiles.open(processed_file_path, 'r', encoding='utf-8') as file:
                html_content = await file.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            page_links = soup.find_all('a', href=lambda x: x and x.startswith("/prematch/leagues"))
            for page_link in page_links:
                full_url = base_url + page_link['href']
                num_segments = len(full_url.split('/')) - 2  # Adjust based on your URL structure
                if not any(word in full_url for word in excluded_words) and 1 <= num_segments < 10:
                    new_unique_links.add(full_url)
        except Exception as e:
            print(f"Error extracting new unique links: {e}")
        return list(new_unique_links)

    async def process_links(file_path, output_file, base_url, excluded_words):
        unique_links = set()
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            links = [line.strip() for line in await file.readlines()]
        for link in links:
            content = await fetch_and_process_url(link, random.randint(3, 6), random.uniform(0.25, 0.75))
            await save_content_to_file(output_file, content + '\n\n', 'a')
        return links  # Return the original links for comparison

    async def process_final_links(file_path, output_file):
    # Ensure output_file (tonybet.html) is cleared at the start
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as file:
            pass  # This clears 'tonybet.html'

        # Process links from 'tonybet_links_v2.txt'
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            links = [line.strip() for line in await file.readlines()]
        for link in links:
            content = await fetch_and_process_url(link, random.randint(3, 6), random.uniform(0.25, 0.75))
            # Append content to 'tonybet.html'
            await save_content_to_file(output_file, content + '\n\n', 'a')

    # Main process starts here
    base_url = 'https://tonybet.es'
    excluded_words = ['search', 'live', 'null']

    original_links = await process_links(ROOT_DIR / 'tonybet/tonybet_links.txt', ROOT_DIR / 'tonybet/tonybet_links.html', base_url, excluded_words)
    new_unique_links = await extract_new_unique_links(ROOT_DIR / 'tonybet/tonybet_links.html', base_url, excluded_words, set(original_links))
    await save_content_to_file(ROOT_DIR / 'tonybet/tonybet_links_v2.txt', '\n'.join(new_unique_links), 'w')
    await process_final_links(ROOT_DIR / 'tonybet/tonybet_links_v2.txt', ROOT_DIR / 'tonybet/tonybet.html')
    print('Tonybet')


def scrape_winamax():
    url = 'https://www.winamax.es/apuestas-deportivas'
    cookies = {
        
        }

    response = requests.get(url, cookies=cookies)

    if response.status_code == 200:
        with open(ROOT_DIR / 'winamax/winamax.html', 'w', encoding='utf-8') as html_file:
            html_file.write(response.text)

        soup = BeautifulSoup(response.text, 'html.parser')

        script_tags = soup.find_all('script', {'type': 'text/javascript'})
        preloaded_state = None

        for script in script_tags:
            if 'PRELOADED_STATE' in script.text:
                json_str = script.text.split('=', 1)[1].strip()
                json_str = json_str.rstrip(';')
                try:
                    preloaded_state = json.loads(json_str)
                    break
                except json.decoder.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")

        if preloaded_state:
            print("JSON data extracted successfully!")
            
            matches_data = preloaded_state.get('matches', {})
            bets_data = preloaded_state.get('bets', {})
            outcomes_data = preloaded_state.get('outcomes', {})
            odds_data = preloaded_state.get('odds', {})
            
            match_ids = matches_data.keys()  # Assuming the match IDs are the keys of the 'matches' dictionary
            
            with open(ROOT_DIR / 'winamax/winamax.txt', 'w', encoding='utf-8') as archivo_salida:
                for match_id, match_info in matches_data.items():
                    # Check if the match status is 'PREMATCH'
                    if match_info.get('status') == 'PREMATCH':
                        teams = match_info.get('title', 'Unknown Match').split(' - ')
                        teams = [clean_name(team) for team in teams]

                        if len(teams) != 2:
                            continue  # Skip if not exactly two teams

                        main_bet_id = match_info.get('mainBetId')
                        bet_info = bets_data.get(str(main_bet_id), {})
                        outcome_ids = bet_info.get('outcomes', [])

                        # Check if odds are available for this match
                        odds_available = any(odds_data.get(str(outcome_id)) for outcome_id in outcome_ids)

                        if odds_available:
                            archivo_salida.write(f"{teams[0]} - {teams[1]}\n")
                            for i, outcome_id in enumerate(outcome_ids, start=1):
                                odds_value = odds_data.get(str(outcome_id), 'No odds available')
                                archivo_salida.write(f"  {i}: {odds_value}\n")
                            archivo_salida.write("-----\n")
        else:
            print("PRELOADED_STATE not found in the HTML.")
    else:
        print(f'Error while making the request. Response code: {response.status_code}')


async def scrape_zebet_async():
    url = 'https://www.zebet.es'

    cookies = {
    
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, max_redirects=10, cookies=cookies) as response:
            if response.status == 200:
                text = await response.text()
                async with aiofiles.open(ROOT_DIR / 'zebet/zebet_links.html', 'w', encoding='utf-8') as file:
                    await file.write(text)
            else:
                print(f'Error while making the request. Response code: {response.status}')

        async with aiofiles.open(ROOT_DIR / 'zebet/zebet_links.html', 'r', encoding='utf-8') as file:
            content = await file.read()
            soup = BeautifulSoup(content, 'html.parser')
            links = soup.find_all('a', href=re.compile('^/es/competition'))
            unique_links = set()

            async with aiofiles.open(ROOT_DIR / 'zebet/zebet_links.txt', 'w', encoding='utf-8') as outfile:
                for link in links:
                    full_url = url + link['href']
                    if full_url not in unique_links:
                        await outfile.write(full_url + '\n')
                        unique_links.add(full_url)

        async with aiofiles.open(ROOT_DIR / 'zebet/zebet.html', 'w', encoding='utf-8') as file:
            await file.write('')

        async with aiofiles.open(ROOT_DIR / 'zebet/zebet_links.txt', 'r', encoding='utf-8') as link_file:
            async for url in link_file:
                url = url.strip()
                await asyncio.sleep(random.uniform(1.55, 2.85))
                async with session.get(url, max_redirects=10, cookies=cookies) as response:
                    if response.status == 200:
                        text = await response.text()
                        async with aiofiles.open(ROOT_DIR / 'zebet/zebet.html', 'a', encoding='utf-8') as html_file:
                            await html_file.write(text + '\n')
                    else:
                        print(f'Error while making the request to {url}. Response code: {response.status}')

        async with aiofiles.open(ROOT_DIR / 'zebet/zebet.html', 'r', encoding='utf-8') as archivo:
            html_content = await archivo.read()

        soup = BeautifulSoup(html_content, 'html.parser')

        async with aiofiles.open(ROOT_DIR / 'zebet/zebet.txt', 'w', encoding='utf-8') as archivo_salida:
            bloques = soup.find_all(class_=re.compile(r'item-bloc-type-\d+'))

            for bloque in bloques:
                data_found = False

                nombre_enfrentamiento_element = bloque.find(class_='uk-visible-small uk-text-bold uk-margin-left uk-text-truncate')
                if nombre_enfrentamiento_element:
                    nombre_enfrentamiento = nombre_enfrentamiento_element.text.strip()
                    nombre_enfrentamiento = clean_name(nombre_enfrentamiento)
                    nombre_enfrentamiento = nombre_enfrentamiento.replace(' / ', ' - ')  # Replace slashes with dashes
                    await archivo_salida.write(f"{nombre_enfrentamiento}\n")
                    data_found = True

                resultados = bloque.find_all(class_=re.compile(r"^bet-actor(?!odd)[\dN]\b.*uk-visible-small"))
                if resultados:
                    contador_resultados = 1
                    for resultado in resultados:
                        odd = resultado.find('span', class_='pmq-cote')
                        if odd:
                            odd = odd.text.strip().replace(',', '.')  # Normalize the odds values
                            await archivo_salida.write(f"  {contador_resultados}: {odd}\n")
                            contador_resultados += 1
                            data_found = True

                # Check if 'bet-activebets' div exists before finding the 'a' tag
                event_link_element = bloque.find('div', class_='bet-activebets')
                if event_link_element:
                    event_link_a = event_link_element.find('a', href=True)
                    if event_link_a:
                        event_link = url + event_link_a['href']
                        await archivo_salida.write(f"link -> {event_link}\n")
                        data_found = True

                if data_found:
                    await archivo_salida.write("-----\n")
    print('Zebet')


# Function to extract the event link from a block of text
def extract_event_link(block):
    match = re.search(r'link -> (.+)', block)
    return match.group(1) if match else None

# Function to get or create an event match and return its ID
def get_or_create_event_match(cursor, event_name):
    try:
        # Check if the event match already exists
        cursor.execute("SELECT EventMatchID FROM EventMatches WHERE UniversalEventName = ?", (event_name,))
        match = cursor.fetchone()
        if match:
            return match[0]  # Return the existing EventMatchID
        else:
            # If not, create a new event match record
            cursor.execute("INSERT INTO EventMatches (UniversalEventName) VALUES (?)", (event_name,))
            return cursor.lastrowid  # Return the new EventMatchID
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return None


# Insert event record and return its ID
def get_or_create_event(cursor, event_name, event_match_id):
    try:
        # Check if the event already exists with the same EventMatchID
        cursor.execute("SELECT EventID FROM Events WHERE EventName = ? AND EventMatchID = ?", (event_name, event_match_id))
        event = cursor.fetchone()
        if event:
            return event[0]  # Return the existing EventID
        else:
            # If not, create a new event record without the link
            cursor.execute("INSERT INTO Events (EventName, EventMatchID) VALUES (?, ?)", (event_name, event_match_id))
            return cursor.lastrowid  # Return the new EventID
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return None


# Insert outcomes and odds with event link
def insert_outcomes_and_odds(cursor, event_id, outcomes, bookie_name, event_link):
    try:
        for outcome_desc, odds in outcomes:
            # Insert into Outcomes with the EventLink
            cursor.execute("INSERT INTO Outcomes (EventID, OutcomeDescription, EventLink) VALUES (?, ?, ?)", 
                           (event_id, outcome_desc, event_link))
            outcome_id = cursor.lastrowid
            # Insert into Odds with the EventLink
            cursor.execute("INSERT INTO Odds (OutcomeID, BookieName, OfferedOdds, EventLink) VALUES (?, ?, ?, ?)", 
                           (outcome_id, bookie_name, odds, event_link))
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")


def process_bookie_file(filepath, cursor):
    bookie_name = os.path.splitext(os.path.basename(filepath))[0]
    with open(filepath, 'r', encoding='utf-8') as file:
        event_blocks = file.read().strip().split('-----')
        for block in event_blocks:
            if not block.strip():  # Skip empty blocks
                continue
            parts = block.strip().split('\nlink ->', 1)  # Split the block to separate the link
            event_block = parts[0].strip()
            event_lines = event_block.split('\n')
            event_name = event_lines[0]
            event_link = extract_event_link(block) if len(parts) == 2 else "No link provided"
            event_match_id = get_or_create_event_match(cursor, event_name)
            event_id = get_or_create_event(cursor, event_name, event_match_id)
            if event_id is not None:
                outcomes = []
                for line in event_lines[1:]:  # Iterate over the lines excluding the event name
                    try:
                        split_line = line.split(':')
                        if len(split_line) != 2 or not split_line[1].strip():
                            print(f"Line format error in {line}: {bookie_name}")
                            continue

                        outcome_num, odd = split_line
                        outcome_desc = f"{outcome_num.strip()}"
                        odd = float(odd.strip())
                        outcomes.append((outcome_desc, odd))
                    except ValueError as e:
                        print(f"Error parsing line {line}: {e} {bookie_name}")
                        continue
                insert_outcomes_and_odds(cursor, event_id, outcomes, bookie_name, event_link)


def clear_existing_data(cursor):
    try:
        cursor.execute("DELETE FROM Odds")
        cursor.execute("DELETE FROM Outcomes")
        cursor.execute("DELETE FROM Events")
        cursor.execute("DELETE FROM EventMatches")
    except sqlite3.DatabaseError as e:
        print(f"Database error while clearing data: {e}")


# Main function to walk through the directories and process files
def process_directories(root_dir):
    with sqlite3.connect(ROOT_DIR / 'odds.db') as conn:
        cursor = conn.cursor()
        clear_existing_data(cursor)  # Clear existing data before processing new files
        for subdir, dirs, files in os.walk(root_dir):
            folder_name = os.path.basename(subdir)
            for filename in files:
                if filename.endswith('.txt') and os.path.splitext(filename)[0] == folder_name:
                    filepath = os.path.join(subdir, filename)
                    try:
                        process_bookie_file(filepath, cursor)
                    except Exception as e:
                        print(f"An error occurred while processing file {filepath}: {e}")
        conn.commit()

def metaphone_tokenized(event_name):
    tokens = word_tokenize(event_name.lower())
    phonetic_tokens = [metaphone(token) for token in tokens]
    return set(phonetic_tokens)

def match_events(event_phonetics, new_event_phonetics, event_names, new_event_name, threshold=SIMILARITY_THRESHOLD):
    for existing_event, phonetics_set in event_phonetics.items():
        if phonetics_set & new_event_phonetics:
            similarity = fuzz.token_sort_ratio(event_names[existing_event], new_event_name)
            if similarity > threshold:
                return existing_event
    return None

# Function to query the database and process the results into a dictionary
def get_max_odds_from_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        E.EventName,
        O.OutcomeDescription,
        MAX(OD.OfferedOdds) AS MaxOfferedOdds,
        (SELECT GROUP_CONCAT(OD2.BookieName) 
        FROM Odds OD2 
        WHERE OD2.OutcomeID = O.OutcomeID AND OD2.OfferedOdds = MAX(OD.OfferedOdds)) AS BookiesWithMaxOdds,
        OD.EventLink  
    FROM 
        Events E
    JOIN 
        Outcomes O ON E.EventID = O.EventID
    JOIN 
        Odds OD ON O.OutcomeID = OD.OutcomeID
    GROUP BY 
        E.EventName, 
        O.OutcomeDescription
    ORDER BY 
        E.EventName
    """)

    results = cursor.fetchall()
    conn.close()
    return results

def process_chunk(chunk):
    event_phonetics = {}
    event_names = {}
    grouped_events = defaultdict(list)
    unified_results = []

    for event_name, outcome_description, max_odds, bookies_with_max_odds, event_link in chunk:
        event_phonetic_tokens = metaphone_tokenized(event_name)
        best_match = match_events(event_phonetics, event_phonetic_tokens, event_names, event_name)

        if best_match:
            unified_event_name = best_match
        else:
            unified_event_name = event_name
            event_phonetics[unified_event_name] = event_phonetic_tokens
            event_names[unified_event_name] = event_name

        grouped_events[unified_event_name].append(event_name)
        unified_results.append((unified_event_name, outcome_description, max_odds, bookies_with_max_odds, event_link))  # Add the event_link here

    return unified_results, grouped_events

def chunk_data(results):
    chunks = []
    current_chunk = []
    current_letter = None

    for result in results:
        event_name = result[0]
        if current_letter is None or event_name[0].lower() == current_letter:
            current_chunk.append(result)
        else:
            chunks.append(current_chunk)
            current_chunk = [result]
        current_letter = event_name[0].lower()

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def unify_event_names_parallel(results):
    chunks = chunk_data(results)

    with Pool(N_PROCESSES) as pool:
        results = pool.map(process_chunk, chunks)

    # Combine results from all chunks
    unified_results = []
    grouped_events = defaultdict(list)
    for result in results:
        unified_chunk_results, grouped_chunk_events = result
        unified_results.extend(unified_chunk_results)
        for event_name, events in grouped_chunk_events.items():
            grouped_events[event_name].extend(events)

    return unified_results, grouped_events

# Function to write the max odds to a file in the desired format
def write_max_odds_to_file(max_odds_dict, grouped_events, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for unified_event_name, associated_events in grouped_events.items():
            file.write(f"{unified_event_name} (Grouped Events: {', '.join(associated_events)}):\n")
            for outcome_desc, (max_odds, bookies, link) in max_odds_dict[unified_event_name].items():  # Expect a tuple with the link now
                file.write(f"{outcome_desc}: {max_odds} --> {bookies} -> {link}\n")  # Output the link
            file.write("----------\n")

# Function to calculate stakes for the equal pay strategy
def calculate_stakes_equal_pay(odds, probability, amount_to_bet):
    return [(probability / odd) * amount_to_bet for odd in odds]

# Function to calculate stakes for the max risk strategy
def calculate_stakes_max_risk(inverse_odds, odds, amount_to_bet):
    max_odd_index = inverse_odds.index(min(inverse_odds))
    sum_of_other_stakes = sum(inverse_odd * amount_to_bet for i, inverse_odd in enumerate(inverse_odds) if i != max_odd_index)
    
    stakes = [inverse_odd * amount_to_bet if i != max_odd_index else amount_to_bet - sum_of_other_stakes for i, inverse_odd in enumerate(inverse_odds)]
    return stakes

def write_strategy_to_file(file, stakes, total_profit, strategy_title):
    file.write(strategy_title + "\n")
    for i, stake in enumerate(stakes):
        file.write(f"Stake for bet {i+1}: {stake:,.2f}$\n")
    file.write(f"Total profit: {total_profit:,.2f}$\n")
    file.write("-------------------------\n")

# Function to calculate the arbitrage probability
def arb_calculator(odds):
    odds_probability = sum(1/odd for odd in odds)
    return 1 / odds_probability if odds_probability < 1 else "Not arbitrageable"

def async_wrapper(async_func):
    """Executes an async function within a new event loop."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_func())
        loop.close()
        return result
    except Exception as e:
        func_name = async_func.__name__ if hasattr(async_func, '__name__') else 'Unknown function'
        print(f"Error executing {func_name}: {e}")

def execute_in_parallel(async_funcs):
    """Executes given async functions in parallel using multiprocessing."""
    max_workers = ceil(os.cpu_count() * 0.75) or 1
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Map each async function through the async_wrapper
        futures = [executor.submit(async_wrapper, func) for func in async_funcs]
        for future in futures:
            print(future.result())  # Here for debugging; adjust as needed

if __name__ == "__main__":
    start_time = time.time()

    # Direct references to your async functions
    async_funcs = [
        #scrape_1xbet_async, NOT WORKING ANYMORE. NEED TO PASS "PROOF THAT YOU ARE A HUMAN" AFTER FIRST REQUEST, WHICH I HAVE NO IDEA HOW TO DO IT. 
        scrape_777_async,
        scrape_betfair_async,
        scrape_bwin_async,
        scrape_dafabet_async,
        #scrape_interwetten_async, WORKED UP UNTIL MAY 2024. Suddenly Error 403.
        #scrape_marathonbet_async, WORKED UP UNTIL MAY 2024. 
        scrape_marca_async,
        scrape_pokerstars_async,
        scrape_zebet_async
    ]

    execute_in_parallel(async_funcs)

    end_time = time.time()
    print(f"Time taken for scraping: {end_time - start_time:.2f} seconds.")
    minutes = (end_time - start_time) / 60
    print(f"Time taken for scraping: {minutes:.2f} minutes.")

    # Start timing for processing directories to write_max_odds_to_file
    processing_start_time = time.time()
    # Call the main function with the path to your top root directory
    process_directories(ROOT_DIR)

    results = get_max_odds_from_db()
    unified_results, grouped_events = unify_event_names_parallel(results)

    max_odds_dict = {}
    for unified_event_name, outcome_description, max_odds, bookies_with_max_odds, event_link in unified_results:  #Include the event_link
        if unified_event_name not in max_odds_dict:
            max_odds_dict[unified_event_name] = {}
        max_odds_dict[unified_event_name][outcome_description] = (max_odds, bookies_with_max_odds, event_link)  # Include the event_link here

    # Write the max odds to maxodds.txt
    write_max_odds_to_file(max_odds_dict, grouped_events, ROOT_DIR / 'maxodds.txt')
    processing_end_time = time.time()
    print(f"Time taken from processing directories to write_max_odds_to_file: {processing_end_time - processing_start_time:.2f} seconds.")

    # Start timing for remaining part of the script
    remaining_part_start_time = time.time()

    with open(ROOT_DIR / 'arbitrageable.txt', 'w') as file:
        for event_name, outcomes in max_odds_dict.items():
            odds = [info[0] for info in outcomes.values()]
            bookies = [info[1] for info in outcomes.values()]
            links = [info[2] for info in outcomes.values()]
            probability = arb_calculator(odds)

            if probability != "Not arbitrageable":
                file.write("-------------------------\n")
                file.write("-------------------------\n")
                file.write(f"{event_name}:\n")
                for i, (outcome_desc, (max_odds, bookies, event_link)) in enumerate(outcomes.items()):
                    file.write(f"{outcome_desc}: {max_odds} --> {bookies} -> {event_link}\n") 
                file.write("-------------------------\n")
                
                stakes_equal_pay = calculate_stakes_equal_pay(odds, probability, AMOUNT_TO_BET)
                total_profit_equal_pay = (probability - 1) * AMOUNT_TO_BET
                write_strategy_to_file(file, stakes_equal_pay, total_profit_equal_pay, "For equal pay strategy:")

                inverse_odds = [1/odd for odd in odds]
                stakes_max_risk = calculate_stakes_max_risk(inverse_odds, odds, AMOUNT_TO_BET)
                total_profit_max_risk = sum((stake * odd) - AMOUNT_TO_BET for stake, odd in zip(stakes_max_risk, odds))
                write_strategy_to_file(file, stakes_max_risk, total_profit_max_risk, "For max risk strategy:")
                file.write("-------------------------\n")
                file.write("\n")

    remaining_part_end_time = time.time()
    print(f"Time taken for remaining part of the script: {remaining_part_end_time - remaining_part_start_time:.2f} seconds.")

    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = (elapsed_time / 60)
    print(f"Script executed in {elapsed_time:.2f} seconds.")
    print(f"Script executed in {minutes:.2f} minutes.")
    