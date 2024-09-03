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

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(scrape_777_async())
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = (elapsed_time / 60)
    print(f"Script executed in {elapsed_time:.2f} seconds.")
    print(f"Script executed in {minutes:.2f} minutes.")