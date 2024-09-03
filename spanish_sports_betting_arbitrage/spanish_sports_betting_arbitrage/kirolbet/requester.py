import requests
from bs4 import BeautifulSoup
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
url = 'https://apuestas.kirolbet.es/'

cookies = {
    }

response = requests.get(url, cookies=cookies)

if response.status_code == 200:

    soup = BeautifulSoup(response.text, 'html.parser')

    with open(ROOT_DIR / 'kirolbet\kirolbet.html', 'w', encoding='utf-8') as file:
        file.write(response.text)
else:
    print(f'Error while making the request. Response code: {response.status_code}')
