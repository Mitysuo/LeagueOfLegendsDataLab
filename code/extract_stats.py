import json

from libs.extract_lib.stats import StatsFetcher
from settings import docs_path

def main():
    # Obtenção dos campeões
    with open(docs_path + '\champions.json', 'r', encoding='utf-8') as file:
        champions = json.load(file)

    champion_ids = [champion_info['key'] for champion_info in champions['data'].values()]
    
    # Obtenção das Runas
    with open(docs_path + r'\runes.json', 'r', encoding='utf-8') as file:
        runes = json.load(file)

    rune_ids = list(runes['data'].keys())
    
    for championId in champion_ids:
        stats = StatsFetcher(champion_id=championId)
        for runeId in rune_ids:
            pass

if __name__ == "__main__":
    main()