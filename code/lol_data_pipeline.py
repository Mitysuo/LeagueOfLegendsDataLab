from datetime import datetime, timedelta
from libs.riot_lib.riot import LeagueOfLegends
from libs.sql_lib.sql import SQLClient

def insert_player_data():
    """Busca informações dos jogadores na API da Riot e insere no banco de dados SQL."""
    lol = LeagueOfLegends(region='BR1', queue='RANKED_SOLO_5x5')
    df_players = lol.get_league(2000)

    sql_client = SQLClient(use_sqlalchemy=False)
    sql_client.insert_dataframe(df_players, 'Players')


def insert_match_data():
    """Busca informações de partidas dos jogadores na API da Riot e insere no banco de dados SQL."""
    lol = LeagueOfLegends(region='BR1', queue='420') # Queue 420: 5v5 Ranked Solo games
    sql_client = SQLClient()
    puuid_list = sql_client.get_data('Players', 'puuid')['puuid'].to_list()

    # Example PUUID for testing
    puuid_list = ['H6sXt63uETotBrVuEmGZHileTX2_bLRdIoYQ4elYU8DRLmLM_eRYSPYLNvrkILKi-J1yYMsZBr4dsw']

    for puuid in puuid_list:
        match_list = lol.get_matchlist(puuid, count=100)

        for match in match_list:
            df_match, df_team, df_playermatches = lol.get_match(match)
            game_version = df_match['gameVersion'][0][:5]
            game_start_timestamp = df_match['gameStartTimestamp'][0]

            match_date = datetime.fromtimestamp(game_start_timestamp / 1000)
            past_three_days = datetime.now() - timedelta(days=3)

            if game_version == '14.20' and match_date > past_three_days:
                sql_client.insert_dataframe(df_match, 'Matches')
                sql_client.insert_dataframe(df_team, 'Teams')
                sql_client.insert_dataframe(df_playermatches, 'PlayerMatches')


if __name__ == "__main__":
    insert_player_data()
    insert_match_data()
