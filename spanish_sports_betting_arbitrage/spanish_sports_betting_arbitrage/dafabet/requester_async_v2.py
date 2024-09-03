import asyncio
from pyppeteer import launch, errors as pyppeteer_errors
from bs4 import BeautifulSoup
import time
import aiofiles
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

async def fetch_and_render(url, browser, retry_count=3):
    for attempt in range(retry_count):
        try:
            page = await browser.newPage()
            await page.goto(url, {'waitUntil': 'networkidle0'})
            content = await page.content()
            await page.close()
            return content
        except pyppeteer_errors.NetworkError as e:
            print(f"Attempt {attempt+1} failed: {str(e)}")
            await page.close()
            if attempt == retry_count - 1:
                raise  # Reraise the last exception if all retries fail

async def extract_links(html, base_url):
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

async def write_links_to_file(links, file_path):
    async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
        for link in links:
            await file.write(link + '\n')

async def append_content_to_file(html, file_path):
    async with aiofiles.open(file_path, 'a', encoding='utf-8') as file:
        await file.write(html + '\n')

async def process_link(url, browser, final_html_file, semaphore):
    async with semaphore:  # Control access to a resource, limiting the number of concurrent tasks
        content = await fetch_and_render(url, browser)
        await append_content_to_file(content, final_html_file)

async def process_links(file_path, browser, final_html_file):
    # Initialize semaphore with a desired number of concurrent tasks, e.g., 10
    semaphore = asyncio.Semaphore(5)

    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        urls = await file.readlines()

    # Convert process_link calls into tasks with the semaphore
    tasks = [process_link(url.strip(), browser, final_html_file, semaphore) for url in urls]

    # Wait for all tasks to be completed
    await asyncio.gather(*tasks)

async def main():
    start_time = time.time()
    browser = await launch()  # Launch browser once at the start

    url = 'https://www.dafabet.es/es/sports'
    base_url = 'https://www.dafabet.es'
    links_file = ROOT_DIR / 'dafabet/dafabet_links.txt'
    final_html_file = ROOT_DIR / 'dafabet/dafabet.html'

    # Initialize or clear the content of dafabet.html
    async with aiofiles.open(final_html_file, 'w', encoding='utf-8') as file:
        await file.write('')  # This empties the file or creates it if it doesn't exist

    content = await fetch_and_render(url, browser)
    links = await extract_links(content, base_url)
    await write_links_to_file(links, links_file)
    await process_links(links_file, browser, final_html_file)

    await browser.close()
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes = (elapsed_time / 60)
    print(f"Script executed in {elapsed_time:.2f} seconds.")
    print(f"Script executed in {minutes:.2f} minutes.")

asyncio.run(main())