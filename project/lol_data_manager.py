from datetime import datetime, timedelta

from tqdm import tqdm

from libs.riot_lib.riot import LeagueOfLegends
from libs.sql_lib.sql import SQLClient
from settings import (
    AMOUNT,
    GAME_VERSION,
    champion_mastery_table,
    match_table,
    player_match_table,
    player_table,
    team_table,
)


class LeagueDataManager:
    def __init__(
        self,
        region="BR1",
        queue="RANKED_SOLO_5x5",
        game_version=GAME_VERSION,
        amount=AMOUNT,
    ):
        self.region = region
        self.queue = queue
        self.game_version = game_version
        self.amount = int(amount)
        self.lol = LeagueOfLegends(region=self.region, queue=self.queue)
        self.sql = SQLClient(use_sqlalchemy=False)

    def get_existing_matches(self, table_name):
        """Obtém os Ids das partidas já inseridas no banco."""
        if self.sql.table_exists(table_name):
            matches = self.sql.get_data(table_name, "matchId")["matchId"].to_list()
            return matches
        return []

    def insert_player_data(self, player_table):
        """Busca informações dos jogadores na API e insere no banco."""
        df_players = self.lol.get_league(self.amount)
        self.sql.insert_dataframe(df_players, player_table)

    def insert_mastery_champions(self):
        """Busca informações de maestria dos campeões e insere no banco."""
        df_player_match_table = self.sql.get_data(
            player_match_table, "puuid, championLevel"
        )
        puuid_list = list(
            set(
                df_player_match_table[df_player_match_table["championLevel"].isnull()][
                    "puuid"
                ].to_list()
            )
        )

        for puuid in tqdm(puuid_list, desc="Obtendo Maestria dos Campeões"):
            try:
                mastery_champions = self.lol.get_mastery_champion(puuid)
                self.sql.insert_dataframe(
                    mastery_champions, champion_mastery_table, ["puuid", "championId"]
                )
            except Exception as e:
                print(f"Erro ao obter maestria para {puuid}: {e}")

    def insert_match_data(self):
        """Busca informações de partidas dos jogadores e insere no banco."""
        puuid_list = self.sql.get_data(player_table, "puuid")["puuid"].tolist()
        existing_matches = self.get_existing_matches(match_table)

        for puuid in tqdm(puuid_list, desc="Interação sobre os jogadores"):
            match_list = self.lol.get_matchlist(puuid, count=2)
            if not match_list:
                continue

            match_list = [
                match for match in match_list if match not in existing_matches
            ]
            for match in tqdm(match_list, desc="Interação das partidas"):
                try:
                    df_match, df_team, df_playermatches = self.lol.get_match(match)
                    if not df_match:
                        continue

                    # Filtrar partidas pela versão e data
                    version = df_match["gameVersion"][0][:5]
                    start_timestamp = df_match["gameStartTimestamp"][0]
                    match_date = datetime.fromtimestamp(start_timestamp)
                    past_seven_days = datetime.now() - timedelta(days=7)

                    if version == self.game_version and match_date >= past_seven_days:
                        self.sql.insert_dataframe(df_match, match_table)
                        self.sql.insert_dataframe(df_team, team_table)
                        self.sql.insert_dataframe(
                            df_playermatches, player_match_table, ["puuid", "matchId"]
                        )
                        existing_matches.append(match)
                except Exception as e:
                    print(f"Erro ao processar partida {match}: {e}")


if __name__ == "__main__":
    manager = LeagueDataManager()

    # Excluir tabelas se existirem
    manager.sql.drop_table(player_table)
    manager.sql.drop_table(champion_mastery_table)

    # Inserir dados de jogadores
    manager.insert_player_data()

    # Inserir dados de partidas
    manager.insert_match_data()

    # Inserir maestria dos campeões
    manager.insert_mastery_champions()
