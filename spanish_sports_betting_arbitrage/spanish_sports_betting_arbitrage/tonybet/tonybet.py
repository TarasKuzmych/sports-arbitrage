from pyppeteer import launch, errors as pyppeteer_errors
from bs4 import BeautifulSoup
import unicodedata
import aiofiles
import asyncio
import random
import time
import re
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('ASCII')

women_categories = {
    'Women': 'Femenino', 'women': 'Femenino', 'Femenino': 'Femenino', ' (W) ': 'Femenino', 'Ladies': 'Femenino'
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
    
    # Split the event name into parts to handle each team separately
    parts = event_name.split(' - ')
    standardized_parts = []

    for part in parts:
        # Check and replace each variation with the standard term
        for variation, standard in category_mapping.items():
            # Skip the specific case that has already been handled
            if variation == '(W)':
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

async def scrape_tonybet_async():
    async def fetch_and_process_url(url, scroll_downs=1, sleep_duration=0.5):
        browser = None
        try:
            browser = await launch()
            page = await browser.newPage()
            await page.goto(url, {'waitUntil': 'networkidle0', 'timeout': 15000})  # Consider including timeout and waitUntil parameters for reliability
            for _ in range(scroll_downs):
                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                await asyncio.sleep(sleep_duration)
            content = await page.content()
            return content
        except pyppeteer_errors.PyppeteerError as e:  # Now using the renamed errors module
            print(f"An error occurred while processing {url}: {e}")
            return ""  # Return an empty string or handle the error as appropriate for your application
        finally:
            if browser:
                await browser.close()

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

    async def read_html_file(file_path):
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
        return content

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

    base_url = 'https://tonybet.es'
    excluded_words = ['search', 'live', 'null']
    
    original_links = await process_links(ROOT_DIR / 'tonybet/tonybet_links.txt', ROOT_DIR / 'tonybet/tonybet_links.html', base_url, excluded_words)
    new_unique_links = await extract_new_unique_links(ROOT_DIR / 'tonybet/tonybet_links.html', base_url, excluded_words, set(original_links))
    await save_content_to_file(ROOT_DIR / 'tonybet/tonybet_links_v2.txt', '\n'.join(new_unique_links), 'w')
    await process_final_links(ROOT_DIR / 'tonybet/tonybet_links_v2.txt', ROOT_DIR / 'tonybet/tonybet.html')
    print('Tonybet Requests Completed')

    # Adapted BeautifulSoup processing for asynchronous execution
    ruta_archivo = ROOT_DIR / 'tonybet/tonybet.html'
    archivo_resultados = ROOT_DIR / 'tonybet/tonybet.txt'
    seen_titles = set()

    async with aiofiles.open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        html_content = await archivo.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    async with aiofiles.open(archivo_resultados, 'w', encoding='utf-8') as archivo_salida:
        # Handling original event structure
        event_sections = soup.find_all('div', class_='event-table__row')
        for event_section in event_sections:
            team_names = event_section.find_all('div', class_='event-table__team-name')
            if len(team_names) == 2:
                event_name = f"{team_names[0].get_text(strip=True)} - {team_names[1].get_text(strip=True)}"
            else:
                event_name = ' - '.join([name.get_text(strip=True) for name in team_names])

            if event_name in seen_titles:
                continue
            else:
                seen_titles.add(event_name)

            odds_elements = event_section.find_all('div', class_=lambda x: x and 'outcome' in x and 'decimal' in x)

            odds = [odd_element.get_text(strip=True) for odd_element in odds_elements if odd_element.get_text(strip=True)]

            if not odds:
                continue
            
            clean_event_name = event_name 
            await archivo_salida.write(f"{clean_event_name}\n")
            for idx, value in enumerate(odds, start=1):
                await archivo_salida.write(f"  {idx}: {value}\n")
            await archivo_salida.write("-----\n")

        # Additional handling for new event structures
        top_event_sections = soup.find_all(['div', 'a'], class_='top-events__event-factors')  # Adjust the class name if necessary
        for event_section in top_event_sections:
            team_names = event_section.previous_sibling.find_all('div', class_='top-events__event-team')  # Adjust based on actual structure
            event_name = ' - '.join([team.get_text(strip=True) for team in team_names if team.get_text(strip=True)])

            if event_name in seen_titles:
                continue
            else:
                seen_titles.add(event_name)

            odds_elements = event_section.find_all('div', class_='top-events__event-factor-value')  # Adjust the class name if necessary

            odds = [odd_element.get_text(strip=True) for odd_element in odds_elements if odd_element.get_text(strip=True)]

            if not odds:
                continue

            clean_event_name = clean_name(event_name) 
            await archivo_salida.write(f"{clean_event_name}\n")
            for idx, value in enumerate(odds, start=1):
                await archivo_salida.write(f"  {idx}: {value}\n")
            await archivo_salida.write("-----\n")

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(scrape_tonybet_async())
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = (elapsed_time / 60)
    print(f"Script executed in {elapsed_time:.2f} seconds.")
    print(f"Script executed in {minutes:.2f} minutes.")
