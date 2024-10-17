import json

from libs.riot_lib.riot import LeagueOfLegends
from libs.extract_lib.stats import StatsFetcher
from settings import docs_path

def get_json_files():
    lol = LeagueOfLegends()

    # Get json files
    lol.get_data_dragon_json(version='latest', data_type='champion')
    lol.get_data_dragon_json(version='latest', data_type='item')
    lol.get_data_dragon_json(version='latest', data_type='rune_reforged')
    lol.get_data_dragon_json(version='latest', data_type='language')
    lol.get_data_dragon_json(version='6.24.1', data_type='mastery')
    lol.get_data_dragon_json(version='latest', data_type='profile_icon')
    lol.get_data_dragon_json(version='6.24.1', data_type='rune')
    lol.get_data_dragon_json(version='latest', data_type='summoner_spells')
    lol.get_data_dragon_json(version='latest', data_type='map')

def main():
    # Obtenção dos campeões
    with open(docs_path + '\champion.json', 'r', encoding='utf-8') as file:
        champions = json.load(file)

    champion_ids = [champion_info['key'] for champion_info in champions['data'].values()]
    
    # Obtenção das Runas
    with open(docs_path + r'\rune_reforged.json', 'r', encoding='utf-8') as file:
        runes = json.load(file)

    primary_rune_ids = []
    secundary_rune_ids = []
    for rune in runes:
        primary_rune_ids.append(rune["id"])
        secundary_rune_ids.append([rune["id"] for slot in rune["slots"] for rune in slot["runes"]])
    
    for championId in champion_ids:
        stats = StatsFetcher(championId)
        for rune_id in primary_rune_ids:
            try:
                print(stats.get_rune_stats(rune_id))
            except Exception as e:
                print(e)
        for secundary_rune_id in secundary_rune_ids:
            try:
                print(stats.get_secundary_rune_stats(secundary_rune_id))
            except Exception as e:
                print(e)
        break

if __name__ == "__main__":
    # get_json_files()
    main()