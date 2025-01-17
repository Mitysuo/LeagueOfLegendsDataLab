import pandas as pd
import numpy as np
from tqdm import tqdm

from libs.sql_lib.sql import SQLClient
from settings import player_match_table


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

        perk_average_win_rate = df_rune_win_rate[
            (df_rune_win_rate['championId'] == str(championId))
        ][[perkKeystone, perkPrimaryRow1, perkPrimaryRow2, perkPrimaryRow3, perkSecondaryRow1, perkSecondaryRow2]].replace(-1, np.nan).mean(axis=1).iloc[0]

        perk_average_pick_rate = df_rune_pick_rate[
            (df_rune_pick_rate['championId'] == str(championId))
        ][[perkKeystone, perkPrimaryRow1, perkPrimaryRow2, perkPrimaryRow3, perkSecondaryRow1, perkSecondaryRow2]].replace(-1, np.nan).mean(axis=1).iloc[0]
        
        if np.isnan(perk_average_win_rate):
            perk_average_win_rate = -1.0

        if np.isnan(perk_average_pick_rate):
            perk_average_pick_rate = -1.0

        map_lane = {
            'BOTTOM' : 'adc',
            'UTILITY' : 'support',
            'MIDDLE' : 'mid',
            'TOP' : 'top',
            'JUNGLE' : 'jungle'
        }

        if individualPosition != 'Invalid':
            champion_win_pick_rate = df_champion_stats[
                (df_champion_stats['championId'] == str(championId)) &
                (df_champion_stats['lane'] == map_lane[individualPosition])
            ]

            champion_pick_rate = champion_win_pick_rate['pickRate'].iloc[0]
            champion_win_rate = champion_win_pick_rate['winRate'].iloc[0]
        else:
            champion_pick_rate = -1.0
            champion_win_rate = -1.0
        try:
            championLevel = champion_info['championLevel'].iloc[0]
            championPoints = champion_info['championPoints'].iloc[0]
        except Exception as e:
            print(e)
            championLevel = -1.0
            championPoints = -1.0

        data_to_update.append({'puuid': puuid,
                               'matchId': row['matchId'],
                               'championLevel' : championLevel,
                               'championPoints' : championPoints,
                               'runeWinRate' : perk_average_win_rate,
                               'runePickRate' : perk_average_pick_rate,
                               'championWinRate' : champion_win_rate,
                               'championPickRate' : champion_pick_rate
        })

    df_updates = pd.DataFrame(data_to_update)
    match_columns = ['puuid', 'matchId']

    sql = SQLClient(use_sqlalchemy=False)
    sql.update_data(df_updates, player_match_table, match_columns)

if __name__ == "__main__":
    update_mastery_champions()