from datetime import datetime, timedelta
from libs.riot_lib.riot import LeagueOfLegends
from libs.sql_lib.sql import SQLClient
from tqdm import tqdm

from settings import AMOUNT, GAME_VERSION, match_table, player_table, team_table, player_match_table

def get_matches():
    """Obtém os Ids das partidas já inseridas no banco"""
    sql = SQLClient()
    matches = []
    if sql.table_exists(match_table):
        matches = sql.get_data(match_table, 'matchId')['matchId'].to_list()
    return matches

def insert_player_data(best_players_quantity: int = int(AMOUNT)):
    """Busca informações dos jogadores na API da Riot e insere no banco de dados SQL."""
    lol = LeagueOfLegends(region='BR1', queue='RANKED_SOLO_5x5')
    df_players = lol.get_league(best_players_quantity)

    sql = SQLClient(use_sqlalchemy=False)
    # Alterar para update_dataframe
    sql.insert_dataframe(df_players, player_table)

def insert_mastery_champions():
    sql = SQLClient()
    player_champion_mastery = sql.get_data('PlayerChampionMastery', 'puuid')['puuid'].tolist()
    player_champion_mastery = list(set(player_champion_mastery))
    df_player_match_table = sql.get_data(player_match_table, 'puuid, championLevel')

    puuid_list = df_player_match_table[df_player_match_table['championLevel'].isnull()]['puuid'].to_list()
    # Remover duplicatas
    puuid_list = list(set(puuid_list))
    puuid_list = [puuid for puuid in puuid_list if puuid not in player_champion_mastery]
    
    lol = LeagueOfLegends(region='BR1', queue='RANKED_SOLO_5x5')
    for puuid in tqdm(puuid_list, desc="Obtendo Maestria dos Campeões"):
        try:
            mastery_champions = lol.get_mastery_champion(puuid)
            sql = SQLClient(use_sqlalchemy=False)
            sql.insert_dataframe(mastery_champions, 'PlayerChampionMastery', ['puuid', 'championId'])
        except Exception as e:
            print(e)

def insert_match_data():
    """Busca informações de partidas dos jogadores na API da Riot e insere no banco de dados SQL."""
    lol = LeagueOfLegends(region='BR1', queue='420') # Queue 420: 5v5 Ranked Solo games
    sql = SQLClient(use_sqlalchemy=False)
    puuid_list = sql.get_data('Players', 'puuid')['puuid'].tolist()
    puuid_list = [puuid[0] for puuid in puuid_list][::-1]

    matches_ids = get_matches()
    for puuid in tqdm(puuid_list, desc="Interação sobre os jogadores"):
        match_list = lol.get_matchlist(puuid, count=30)

        if match_list == False:
            continue
        
        match_list = [match for match in match_list if match not in matches_ids]
        for match in tqdm(match_list, desc="Interação das partidas"):
            df_match, df_team, df_playermatches = lol.get_match(match)

            if df_match is False or (matches_ids and match in matches_ids):
                continue

            # Informações da Partida
            version = df_match['gameVersion'][0][:5]
            start_timestamp = df_match['gameStartTimestamp'][0]

            match_date = datetime.fromtimestamp(start_timestamp)
            past_seven_days = datetime.now() - timedelta(days=7)

            if version == GAME_VERSION and match_date >= past_seven_days:
                sql.insert_dataframe(df_match, match_table)
                sql.insert_dataframe(df_team, team_table)
                sql.insert_dataframe(df_playermatches, player_match_table, ['puuid', 'matchId'])

            matches_ids.append(match)


if __name__ == "__main__":
    sql = SQLClient(use_sqlalchemy=False)
    sql.drop_table(player_table)
    sql.drop_table('PlayerChampionMastery')

    insert_player_data()
    
    insert_match_data()
    insert_mastery_champions()
