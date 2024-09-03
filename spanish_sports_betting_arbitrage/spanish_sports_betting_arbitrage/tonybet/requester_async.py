import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup
import time
import aiofiles
import random
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

async def fetch_and_process_url(url, scroll_downs=1, sleep_duration=0.5):
    browser = await launch()
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'domcontentloaded'})
    for _ in range(scroll_downs):
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await asyncio.sleep(sleep_duration)
    content = await page.content()
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
            num_segments = len(full_url.split('/')) - 1  # Adjust based on your URL structure
            if not any(word in full_url for word in excluded_words) and 0 <= num_segments < 10:
                new_unique_links.add(full_url)
    except Exception as e:
        print(f"Error extracting new unique links: {e}")
    return list(new_unique_links)

async def read_html_file(file_path):
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        content = await file.read()
    return content

async def process_links(file_path, output_file, base_url, excluded_words):
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        links = [line.strip() for line in await file.readlines()]
    for link in links:
        content = await fetch_and_process_url(link, random.randint(3, 6), random.uniform(0.25, 0.75))
        await save_content_to_file(output_file, content + 'END OF THIS REQUEST', 'a')
    return links  # Return the original links for comparison

async def process_final_links(file_path, output_file):
    async with aiofiles.open(output_file, 'w', encoding='utf-8') as file:
       pass  # This clears 'tonybet.html'

    # Process links from 'tonybet_links_v2.txt'
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        links = [line.strip() for line in await file.readlines()]
    for link in links:
        content = await fetch_and_process_url(link, random.randint(3, 6), random.uniform(0.25, 0.75))
        # Append content to 'tonybet.html'
        await save_content_to_file(output_file, content + '\n\n', 'a')

async def main():
    start_time = time.time()

    base_url = 'https://tonybet.es'
    excluded_words = ['search', 'live', 'null']
    
    # Process each link and append content
    original_links = await process_links(ROOT_DIR / 'tonybet/tonybet_links.txt', ROOT_DIR / 'tonybet/tonybet_links.html', base_url, excluded_words)
    
    # Extract new unique links with condition 7 > num_segments >= 3
    new_unique_links = await extract_new_unique_links(ROOT_DIR / 'tonybet/tonybet_links.html', base_url, excluded_words, set(original_links))
    
        # Save new unique links to 'tonybet_links_v2.txt' with condition 7 > num_segments >= 3
    await save_content_to_file(ROOT_DIR / 'tonybet/tonybet_links_v2.txt', '\n'.join(new_unique_links), 'w')

    # Process final links and append content to 'tonybet.html'
    await process_final_links(ROOT_DIR / 'tonybet/tonybet_links_v2.txt', ROOT_DIR / 'tonybet/tonybet.html')

    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = elapsed_time / 60
    print(f"Script executed in {elapsed_time:.2f} seconds.")
    print(f"Script executed in {minutes:.2f} minutes.")

asyncio.run(main())