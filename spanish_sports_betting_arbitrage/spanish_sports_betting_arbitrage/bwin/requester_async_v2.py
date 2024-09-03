import asyncio
from pyppeteer import launch, errors as pyppeteer_errors
from bs4 import BeautifulSoup
import time
import aiofiles
import random
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

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

async def extract_and_save_links(html_content, base_url, file_path, excluded_words, segment_condition=(5, 2)):
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
    semaphore = asyncio.Semaphore(5)

    # Create tasks with semaphore passed to each
    tasks = [process_link(browser, link, output_file, semaphore) for link in links]

    # Wait for all tasks to complete
    await asyncio.gather(*tasks)

async def main():
    start_time = time.time()
    browser = await launch()  # Launch browser once at the start
    
    url = 'https://sports.bwin.es/es/sports?popup=sports'
    base_url = 'https://sports.bwin.es'
    excluded_words = ['mañana', 'directo', 'eventos', 'hoy', 'todas', ' bandy', 'los-', 'cupones']

    html_content = await fetch_and_process_url(browser, url, random.randint(1, 6), random.uniform(0.5, 2.0))
    await save_content_to_file(ROOT_DIR / 'bwin/bwin.html', html_content)
    
    # Extract and save initial links with condition 5 > num_segments >= 2
    await extract_and_save_links(html_content, base_url, ROOT_DIR / 'bwin/bwin_links.txt', excluded_words, segment_condition=(5, 2))
    
    # Process each link and append content
    original_links = await process_links(browser, ROOT_DIR / 'bwin/bwin_links.txt', ROOT_DIR / 'bwin/bwin_links.html', base_url, excluded_words)
    
    # Extract new unique links with condition 7 > num_segments >= 3
    new_unique_links = await extract_new_unique_links(ROOT_DIR / 'bwin/bwin_links.html', base_url, excluded_words, set(original_links))
    
        # Save new unique links to 'bwin_links_v2.txt' with condition 7 > num_segments >= 3
    await save_content_to_file(ROOT_DIR / 'bwin/bwin_links_v2.txt', '\n'.join(new_unique_links), 'w')

    # Process final links and append content to 'bwin.html'
    await process_final_links(browser, ROOT_DIR / 'bwin/bwin_links_v2.txt', ROOT_DIR / 'bwin/bwin.html')

    await browser.close()  # Close browser after all operations are done
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = elapsed_time / 60
    print(f"Script executed in {elapsed_time:.2f} seconds.")
    print(f"Script executed in {minutes:.2f} minutes.")

asyncio.run(main())