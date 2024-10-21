import pandas as pd
import numpy as np
from tqdm import tqdm

from libs.sql_lib.sql import SQLClient
from libs.extract_lib.comp_analyzer import LolTheoryScraper 
from settings import match_table, team_table, player_match_table


def update_comp_stats():
    sql = SQLClient()
    df_player_match = sql.get_data(player_match_table, '*')
    df_match = sql.get_data(match_table, '*')

    matchs = df_match[df_match['CompWinRate'].isnull()]['matchId'].to_list()

    position_order = ['TOP', 'JUNGLE', 'MIDDLE', 'BOTTOM', 'UTILITY']
    df_player_match['individualPosition'] = pd.Categorical(df_player_match['individualPosition'], categories=position_order, ordered=True)

    data_to_update = []

    for match_id in tqdm(matchs, desc="Analise das composições"):
        filtered_players = df_player_match[df_player_match['matchId'] == match_id].sort_values(by=['teamId', 'individualPosition'])
        
        champions = []
        for _, row in filtered_players.iterrows():
            champions.append(row['championId'])
        
        stats = LolTheoryScraper()

        try: 
            risk_value, win_rate = map(lambda value: float(value.replace('%', '')), stats.get_stats(champions).values())
        except Exception as e:
            continue
        else:
            data_to_update.append({'matchId': match_id, 'CompRiskValue': risk_value, 'CompWinRate': win_rate})
        
    df_updates = pd.DataFrame(data_to_update)
    match_columns = ['matchId']

    sql = SQLClient(use_sqlalchemy=False)
    sql.update_data(df_updates, match_table, match_columns)

def update_mastery_champions():
    sql = SQLClient()
    df_player_match = sql.get_data(player_match_table, '*')
    df_player_champion_mastery = sql.get_data('PlayerChampionMastery', '*')
    df_rune_win_rate = sql.get_data('RuneWinRate', '*')
    df_rune_pick_rate = sql.get_data('RunePickRate', '*')
    df_champion_stats = sql.get_data('ChampionStats', '*')

    rows_to_update = df_player_match[df_player_match['championLevel'].isnull()]

    data_to_update = []
    for _, row in tqdm(rows_to_update.iterrows(), desc="Analise das maestrias dos campeões"):

        puuid = row['puuid']
        championId = row['championId']
        perkKeystone = str(row['perkKeystone'])
        perkPrimaryRow1 = str(row['perkPrimaryRow1'])
        perkPrimaryRow2 = str(row['perkPrimaryRow2'])
        perkPrimaryRow3 = str(row['perkPrimaryRow3'])
        perkSecondaryRow1 = str(row['perkSecondaryRow1'])
        perkSecondaryRow2 = str(row['perkSecondaryRow2'])
        individualPosition = row['individualPosition']
       
        champion_info = df_player_champion_mastery[ 
            (df_player_champion_mastery['puuid'] == puuid)
            & (df_player_champion_mastery['championId'] == championId)
        ]

        perk_avarage_win_rate = df_rune_win_rate[
            (df_rune_win_rate['championId'] == str(championId))
        ][[perkKeystone, perkPrimaryRow1, perkPrimaryRow2, perkPrimaryRow3, perkSecondaryRow1, perkSecondaryRow2]].replace(-1, np.nan).mean(axis=1).iloc[0]

        perk_avarage_pick_rate = df_rune_pick_rate[
            (df_rune_pick_rate['championId'] == str(championId))
        ][[perkKeystone, perkPrimaryRow1, perkPrimaryRow2, perkPrimaryRow3, perkSecondaryRow1, perkSecondaryRow2]].replace(-1, np.nan).mean(axis=1).iloc[0]
        
        map_lane = {
            'BOTTOM' : 'adc',
            'UTILITY' : 'support',
            'MIDDLE' : 'mid',
            'TOP' : 'top',
            'JUNGLE' : 'jungle'
        }

        champion_win_pick_rate = df_champion_stats[
            (df_champion_stats['championId'] == str(championId)) &
            (df_champion_stats['lane'] == map_lane[individualPosition])
        ]

        champion_pick_rate = champion_win_pick_rate['pickRate'].iloc[0]
        champion_win_rate = champion_win_pick_rate['winRate'].iloc[0]

        championLevel = champion_info['championLevel'].iloc[0]
        championPoints = champion_info['championPoints'].iloc[0]

        data_to_update.append({'puuid': puuid,
                               'matchId': row['matchId'],
                               'championLevel' : championLevel,
                               'championPoints' : championPoints,
                               'runeWinRate' : perk_avarage_win_rate,
                               'runePickRate' : perk_avarage_pick_rate,
                               'championWinRate' : champion_win_rate,
                               'championPickRate' : champion_pick_rate
        })

    df_updates = pd.DataFrame(data_to_update)
    match_columns = ['puuid', 'matchId']

    sql = SQLClient(use_sqlalchemy=False)
    sql.update_data(df_updates, player_match_table, match_columns)

if __name__ == "__main__":
    update_comp_stats()
    update_mastery_champions()