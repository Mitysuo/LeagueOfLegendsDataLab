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
    sql_alchemy = SQLClient()
    puuid_list = sql_alchemy.get_data('Players', 'puuid')['puuid'].to_list()
    
    for puuid in puuid_list[:1]:
        match_list = lol.get_matchlist(puuid)

        for match in match_list[:1]:
            match_data = lol.get_match(match)
            print(match_data)
