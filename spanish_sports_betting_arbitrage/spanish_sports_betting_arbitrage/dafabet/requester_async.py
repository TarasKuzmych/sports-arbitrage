import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup
import time
import aiofiles
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

async def setup_browser():
    return await launch()

async def fetch_and_render(url, browser):
    page = await browser.newPage()
    await page.goto(url, {'waitUntil': 'networkidle0'})
    content = await page.content()
    await page.close()
    return content

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

async def process_links(file_path, browser, final_html_file):
    # Clear out the final HTML file content at the beginning
    async with aiofiles.open(final_html_file, 'w', encoding='utf-8') as file:
        pass  # Simply opening in 'w' mode clears the file
    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
        urls = await file.readlines()

    for url in urls:
        url = url.strip()
        content = await fetch_and_render(url, browser)
        await append_content_to_file(content, final_html_file)

async def main():
    url = 'https://www.dafabet.es/es/sports'
    base_url = 'https://www.dafabet.es'
    links_file = ROOT_DIR / 'dafabet/dafabet_links.txt'
    final_html_file = ROOT_DIR / 'dafabet/dafabet.html'

    browser = await setup_browser()
    content = await fetch_and_render(url, browser)
    links = await extract_links(content, base_url)
    await write_links_to_file(links, links_file)
    await process_links(links_file, browser, final_html_file)

    await browser.close()

start_time = time.time()
asyncio.run(main())
end_time = time.time()
elapsed_time = end_time - start_time
minutes = (elapsed_time / 60)
print(f"Script executed in {elapsed_time:.2f} seconds.")
print(f"Script executed in {minutes:.2f} minutes.")
