from libs.sql_lib.sql import SQLClient
from libs.extract_lib.comp_analyzer import LolTheoryScraper 
from settings import match_table, team_table, player_match_table


def main():
    sql = SQLClient()
    df_player_match = sql.get_data(player_match_table, '*')
    df_teams = sql.get_data(team_table, '*')
    df_match = sql.get_data(match_table, '*')

    for index, row in df_match.iterrows():
        # Criar um método para o df_player_match com filtro (pegar as informações do player naquela partida)
        pass


if __name__ == "__main__":
    main()