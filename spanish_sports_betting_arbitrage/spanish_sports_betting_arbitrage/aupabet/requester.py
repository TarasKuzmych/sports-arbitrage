import requests
from bs4 import BeautifulSoup
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent
url = 'https://www.aupabet.es'

cookies = {

    }

response = requests.get(url, cookies=cookies)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')

    with open(ROOT_DIR / 'aupabet/aupabet.html', 'w', encoding='utf-8') as file:
        file.write(response.text)
else:
    print(f'Error while making the request. Response code: {response.status_code}')

