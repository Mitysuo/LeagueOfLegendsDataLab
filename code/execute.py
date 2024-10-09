import pandas as pd

from statistics import mean, mode
from collections import deque

from riot_lib.riot import LeagueOfLegends
from sql_lib.sql import SQLClient

### Important informations

# queue 420: 5v5 Ranked Solo games

if __name__ == "__main__":
    # lol = LeagueOfLegends(region='BR1', queue='RANKED_SOLO_5x5')

    # # Get the players information
    # df = lol.get_league(2000)

    # sql = SQLClient(use_sqlalchemy=False)
    # sql.insert_dataframe(df, 'Players')

    # Get the match information
    lol = LeagueOfLegends(region='BR1', queue='420')
    # sql_alchemy = SQLClient()
    # puuid_list = sql_alchemy.get_data('Players', 'puuid')['puuid'].to_list()

    puuid_list = ['H6sXt63uETotBrVuEmGZHileTX2_bLRdIoYQ4elYU8DRLmLM_eRYSPYLNvrkILKi-J1yYMsZBr4dsw']
    
    for puuid in puuid_list:
        match_list = lol.get_matchlist(puuid, count=100)

        # Create lists to store information
        win_rate_list = deque(maxlen=6)
        individualPosition_list = deque(maxlen=6)

        for match in match_list:
            df_match, df_team, df_playermatches = lol.get_match(match)

            win_rate_list.append(df_playermatches['win'][0])
            individualPosition_list.append(df_playermatches['individualPosition'][0])

            gameVersion = df_match['gameVersion'][0][:5]
            players = eval(df_match['participants'][0])

            if gameVersion == '14.18' and len(win_rate_list) == 6:
                df_mastery_champion = lol.get_mastery_champion(puuid)
                champion_mastery = df_mastery_champion.loc[df_mastery_champion['championId'] == df_playermatches['championId'], 'averageGrade'].values[0]
                team = 'blue' if df_playermatches['teamId'] == 100 else 'red'
                position = list(individualPosition_list)[5]
                data = {
                    "matchId" : match,
                    f"win_rate_player_{position}_{team}" : mean(map(bool, list(win_rate_list)[:5])),
                    f"is_main_role_{position}_{team}" : mode(list(individualPosition_list)[:5]) == position,
                    f"tierRank_{position}_{team}" : df_playermatches['tierRank'],
                    f"mastery_champion_{position}_{team}" : champion_mastery
                }

                match_information = pd.DataFrame([data])

                i=2
                for player_id in players:
                    if player_id == puuid:
                        continue
                    player_match_list = lol.get_matchlist(player_id, count=100)

                    try:
                        pos = int(player_match_list.index(match))

                        if pos >= 94:
                            break
                        
                        # Create lists to store information about other players
                        win_rate_player_list = deque(maxlen=6)
                        individualPosition_player_list = deque(maxlen=6)
                        
                        right_bound = pos + 5
                        if pos == 0:
                            left_bound = None
                        else:
                            left_bound = pos - 1

                        for match_player in player_match_list[right_bound : left_bound : -1]:
                            df_match, df_team, df_playermatches = lol.get_match(match)

                            # Get the information about other players
                            win_rate_player_list.append(df_playermatches['win'][0])
                            individualPosition_player_list.append(df_playermatches['individualPosition'][0])

                        df_mastery_champion = lol.get_mastery_champion(player_id)
                        champion_mastery = df_mastery_champion.loc[df_mastery_champion['championId'] == df_playermatches['championId'], 'averageGrade'].values[0]
                        team = 'blue' if df_playermatches['teamId'] == 100 else 'red'
                        position_player = list(individualPosition_player_list)[5]

                        match_information[f'win_rate_player_{position_player}_{team}'] = mean(map(bool, list(win_rate_player_list)[:5]))
                        match_information[f'is_main_role_{position_player}_{team}'] = mode(list(individualPosition_player_list)[:5]) == position_player
                        match_information[f'tierRank_{position_player}_{team}'] = df_playermatches['tierRank']
                        match_information[f'mastery_champion_{position}_{team}'] = df_playermatches['tierRank']
                        i+=1

                    except ValueError:
                        break

                break
            
        # Get the 
        print(match_information)

            # Insert the data
            # sql.insert_dataframe(df_match, 'Matches')
            # sql.insert_dataframe(df_team, 'Teams')
            # sql.insert_dataframe(df_playermatches, 'PlayerMatches')

        # df_mastery = lol.get_mastery_champion(puuid)
        # sql.insert_dataframe(df_mastery, 'ChampionMastery')

