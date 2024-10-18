from datetime import datetime, timedelta
from libs.riot_lib.riot import LeagueOfLegends
from libs.sql_lib.sql import SQLClient

from settings import AMOUNT, match_table, player_table, team_table, player_match_table

def get_matches():
    """Obtém os Ids das partidas já inseridas no banco"""
    sql = SQLClient()
    match_ids = []
    if sql.table_exists(match_table):
        match_ids = sql.get_data(match_table, 'matchId')['matchId'].to_list()
    return match_ids

def insert_player_data(best_players_quantity: int = AMOUNT):
    """Busca informações dos jogadores na API da Riot e insere no banco de dados SQL."""
    lol = LeagueOfLegends(region='BR1', queue='RANKED_SOLO_5x5')
    df_players = lol.get_league(best_players_quantity)

    sql_client = SQLClient(use_sqlalchemy=False)
    # Alterar para update_dataframe
    sql_client.insert_dataframe(df_players, player_table)


def insert_match_data(game_version: str = '14.20'):
    """Busca informações de partidas dos jogadores na API da Riot e insere no banco de dados SQL."""
    lol = LeagueOfLegends(region='BR1', queue='420') # Queue 420: 5v5 Ranked Solo games
    sql_client = SQLClient()
    puuid_list = sql_client.get_data('Players', 'puuid')['puuid'].to_list()

    matches_ids = get_matches()

    # Example PUUID for testing
    puuid_list = ['H6sXt63uETotBrVuEmGZHileTX2_bLRdIoYQ4elYU8DRLmLM_eRYSPYLNvrkILKi-J1yYMsZBr4dsw']

    for puuid in puuid_list:
        match_list = lol.get_matchlist(puuid, count=100)

        for match in match_list:
            df_match, df_team, df_playermatches = lol.get_match(match)
            
            # Informações da Partida
            id = df_match['matchId']
            version = df_match['gameVersion'][0][:5]
            start_timestamp = df_match['gameStartTimestamp'][0]

            match_date = datetime.fromtimestamp(start_timestamp / 1000)
            past_three_days = datetime.now() - timedelta(days=3)

            if id in matches_ids:
                continue

            if version == game_version and match_date > past_three_days:
                sql_client.insert_dataframe(df_match, match_table)
                sql_client.insert_dataframe(df_team, team_table)
                sql_client.insert_dataframe(df_playermatches, player_match_table)

                matches_ids.append(id)


if __name__ == "__main__":
    insert_player_data()
    insert_match_data()
