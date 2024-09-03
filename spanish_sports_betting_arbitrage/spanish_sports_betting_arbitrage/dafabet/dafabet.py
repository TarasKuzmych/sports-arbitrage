import asyncio
from pyppeteer import launch, errors as pyppeteer_errors
from bs4 import BeautifulSoup
import aiofiles
import unicodedata
import time
import re
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

# Shared utility functions
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

if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(scrape_dafabet_async())
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = (elapsed_time / 60)
    print(f"Script executed in {elapsed_time:.2f} seconds.")
    print(f"Script executed in {minutes:.2f} minutes.")