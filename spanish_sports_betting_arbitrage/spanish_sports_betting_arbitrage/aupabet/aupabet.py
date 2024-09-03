import requests
from bs4 import BeautifulSoup
import unicodedata
import re
from pathlib import Path

# Define the root directory
ROOT_DIR = Path(__file__).resolve().parent

def remove_accents(input_str):
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    only_ascii = nfkd_form.encode('ASCII', 'ignore')
    return only_ascii.decode('ASCII')


def clean_name(name):
    # Remove all text within parentheses including the parentheses
    name = re.sub(r'\(.*?\)', '', name)

    name = remove_accents(name)

    # List of prefixes and suffixes to remove
    to_remove = ['CSD', 'Atl', 'Ind', 'S.A', 'SSD', 'Baloncesto', 'Hotspur', 'GF', 'BM', 'Zacatecoluca', 'LUK', 'Women', 'Atsmon Playgrounds', 'Rio', 'Basket', 'WKS', 'Cazoo', 'Vitoria Gasteiz', 'Femenino', 'NIS', 'OPAP Athens', 'AD', 'Cs', 'OK', 'KK', 'FC', 'CF', 'CD', 'EC', 'SE', 'MG', 'FK', 'KF', 'AC', 'BK', 'TC', 'NK', 'SD', 'RJ', 'MT', 'BA', 'GO', 'SP', 'CE', 'SC', 'SV', 'RC', 'GC', 'AS', 'SS', 'UD', 'SK', 'CA', 'SL', 'AFC', 'CSC', 'BSC', 'RSC', 'GFC', 'LFC', 'SFC', 'RFC', 'VfL', 'VfB', 'FSV', 'SVW', 'JFC', 'DFC', 'HFC', 'Utd', 'SV', 'RCD', 'FBC', 'PFC', 'TSV', 'EFC', 'CFC', 'BFC', 'JSC', 'OSC', 'RRC', 'CSC', 'GSC', 'HSC', 'MSC', 'SSC', 'VSC', 'WSC', 'ZSC', 'AZ', 'PSV', 'FCZ', 'FCS', 'FCT', 'RKC', 'NAC', 'VVV', 'PEC', 'FCM', 'US', 'AJA', 'AZ', 'RBC', 'TFC', 'WFC', 'IFK', 'GIF', 'BIF', 'AIF', 'MFF', 'AIK', 'DIF', 'HIF', 'ÖFK', 'ÖSK', 'ÖIS', 'GIF', 'AaB', 'BIF', 'FCK', 'OB', 'VB', 'AGF', 'RFC', 'JJK', 'HJK', 'HIFK', 'SJK', 'KTP', 'KPV', 'PS', 'KuPS', 'MYPA', 'VPS', 'FF', 'IF', 'IK', 'BKV', 'BSV', 'B1901', 'B1903', 'B1909', 'B1913', 'KB', 'AB', 'VB', 'LFC', 'BC', 'CB', 'Lfc']

    # Modify the name by removing prefixes and suffixes at the beginning or end
    for item in to_remove:
        # Regular expression for prefix or suffix as a separate word
        word_pattern = r'\b' + re.escape(item) + r'\b'
        name = re.sub(word_pattern, '', name, flags=re.IGNORECASE)

    # Trim and remove extra spaces
    name = ' '.join(name.split())
    return name

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
