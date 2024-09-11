import requests
from bs4 import BeautifulSoup

class RuneStatsFetcher:

    def __init__(self, champion_id) -> None:
        self.champion_id = champion_id
    
    def get_rune_stats(self, rune_id):
        # URL do campeão com base no ID
        url = f"https://leagueofitems.com/champions/{self.champion_id}"
        
        # Fazendo a requisição HTTP para o site
        response = requests.get(url)
        
        # Verificando se a requisição foi bem-sucedida
        if response.status_code != 200:
            raise Exception(f"Failed to load page with status code: {response.status_code}")
        
        # Parsing do conteúdo HTML da página
        soup = BeautifulSoup(response.text, 'html.parser')

        # Procurando a div que contém as informações das runas
        runes_div = soup.find('div', class_='flex w-full space-x-2 overflow-x-auto pb-2')
        
        if not runes_div:
            raise Exception("Couldn't find the runes container div.")
        
        # Procurando a runa específica pelo ID
        rune_link = runes_div.find('a', href=f"/runes/{rune_id}")
        
        if not rune_link:
            raise Exception(f"Couldn't find the rune with ID {rune_id}.")
        
        # Extraindo as estatísticas de winrate e pickrate
        winrate = rune_link.find_all('p')[1].text.strip()
        pickrate = rune_link.find_all('p')[3].text.strip()

        return {
            "winrate": winrate,
            "pickrate": pickrate
        }
    
    def get_secundary_rune_stats(self, secundary_rune_id):
        # URL do campeão com base no ID
        url = f"https://leagueofitems.com/champions/{self.champion_id}"
        
        # Fazendo a requisição HTTP para o site
        response = requests.get(url)
        
        # Verificando se a requisição foi bem-sucedida
        if response.status_code != 200:
            raise Exception(f"Failed to load page with status code: {response.status_code}")
        
        # Parsing do conteúdo HTML da página
        soup = BeautifulSoup(response.text, 'html.parser')

        # Procurando a div que contém as informações das runas
        runes_div = soup.find_all('div', class_='flex w-full space-x-2 overflow-x-auto pb-2')
        
        if not runes_div:
            raise Exception("Couldn't find the runes container div.")
        
        if len(runes_div) >= 2:
            secondary_rune = runes_div[1]
        else:
            raise Exception("Couldn't find the secondary rune div.")
        
        # Procurando a runa específica pelo ID
        secondary_rune_link = secondary_rune.find('a', href=f"/runes/{secundary_rune_id}")
        
        if not secondary_rune_link:
            raise Exception(f"Couldn't find the secondary rune with ID {secundary_rune_id}.")
        
        # Extraindo as estatísticas de winrate e pickrate
        winrate = secondary_rune_link.find_all('p')[1].text.strip()
        pickrate = secondary_rune_link.find_all('p')[3].text.strip()

        return {
            "winrate": winrate,
            "pickrate": pickrate
        }

# Exemplo de uso
champion_id = 266  # Exemplo com Anivia
rune_id = 8143  # Exemplo de ID de runa
fetcher = RuneStatsFetcher(champion_id)
stats = fetcher.get_secundary_rune_stats(rune_id)
print(stats)
