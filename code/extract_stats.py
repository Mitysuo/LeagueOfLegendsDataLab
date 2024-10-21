import os
import json

import pandas as pd
from tqdm import tqdm

from libs.riot_lib.riot import LeagueOfLegends
from libs.extract_lib.stats import StatsFetcher
from libs.sql_lib.sql import SQLClient
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

def get_rune_stats():
    # Obtenção dos ids dos campeões
    with open(docs_path + '\champion.json', 'r', encoding='utf-8') as file:
        champions = json.load(file)

    champion_ids = [champion_info['key'] for champion_info in champions['data'].values()]
    
    # Obtenção das Runas
    with open(docs_path + r'\rune_reforged.json', 'r', encoding='utf-8') as file:
        runes = json.load(file)

    primary_rune_ids = []
    secundary_rune_ids = []
    for rune in runes:
        primary_rune_ids.extend([r["id"] for r in rune["slots"][0]["runes"]])
        secundary_rune_ids.extend([r["id"] for slot in rune["slots"][1:] for r in slot["runes"]])

    win_rate_stats = {}
    pick_rate_stats = {}
    for championId in tqdm(champion_ids, desc="Processando campeões"):
        stats = StatsFetcher(championId)
        for rune_id in primary_rune_ids:
            try:
                win_rate, pick_rate = map(lambda value: float(value.replace('%', '')), stats.get_rune_stats(rune_id).values())
            except Exception as _:
                win_rate, pick_rate = -1.0, -1.0
            finally:
                win_rate_stats[championId][rune_id] = win_rate
                pick_rate_stats[championId][rune_id] = pick_rate
        for secundary_rune_id in secundary_rune_ids:
            try:
                win_rate, pick_rate = map(lambda value: float(value.replace('%', '')), stats.get_secundary_rune_stats(secundary_rune_id).values())
            except Exception as _:
                win_rate, pick_rate = -1.0, -1.0
            finally:
                win_rate_stats[championId][secundary_rune_id] = win_rate
                pick_rate_stats[championId][secundary_rune_id] = pick_rate
        
    df_rune_win_rate = pd.DataFrame.from_dict(win_rate_stats, orient='index')
    df_rune_pick_rate = pd.DataFrame.from_dict(pick_rate_stats, orient='index')

    df_rune_win_rate = df_rune_win_rate.reset_index().rename(columns={'index': 'championId'})
    df_rune_pick_rate = df_rune_pick_rate.reset_index().rename(columns={'index': 'championId'})

    sql = SQLClient(use_sqlalchemy=False)
    sql.insert_dataframe(df_rune_win_rate, 'RuneWinRate', 'championId')
    sql.insert_dataframe(df_rune_pick_rate, 'RunePickRate', 'championId')

def get_champion_stats():
    # Obtenção os ids dos campeões
    with open(docs_path + '\champion.json', 'r', encoding='utf-8') as file:
        champions = json.load(file)

    champion_ids = [champion_info['key'] for champion_info in champions['data'].values()]
    lanes = ['top', 'jungle', 'mid', 'adc', 'support']

    champion_stats = []
    for championId in tqdm(champion_ids, desc="Processando campeões"):
        stats = StatsFetcher(championId)
 
        for lane in lanes:
            try:
                win_rate, pick_rate = map(lambda value: float(value.replace('%', '')), stats.get_champion_stats(lane).values())
                champion_stats.append({
                    'championId': championId,
                    'lane': lane,
                    'winRate': win_rate,
                    'pickRate': pick_rate
                })
            except Exception as _:
                    champion_stats.append({
                        'championId': championId,
                        'lane': lane,
                        'winRate': -1.0,
                        'pickRate': -1.0
                    })

    df_champion_stats = pd.DataFrame(champion_stats)
    sql = SQLClient(use_sqlalchemy=False)
    sql.insert_dataframe(df_champion_stats, 'ChampionStats', ['championId', 'lane'])

if __name__ == "__main__":
    # get_json_files()
    
    # Excluir tabelas se existirem
    sql = SQLClient(use_sqlalchemy=False)
    sql.drop_table('RuneWinRate')
    sql.drop_table('RunePickRate')
    sql.drop_table('ChampionStats')

    get_rune_stats()
    get_champion_stats()
