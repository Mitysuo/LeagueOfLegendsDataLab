import os

import numpy as np
import pandas as pd
from tqdm import tqdm

from libs.sql_lib.sql import SQLClient
from settings import (
    champion_mastery_table,
    champion_stats_table,
    docs_path,
    match_table,
    player_match_table,
    rune_pick_table,
    rune_win_table,
    team_table,
)


class LeagueDataProcessing:
    def __init__(self):
        self.sql = SQLClient()

    def update_mastery_champions(self):
        df_player_match = self.sql.get_data(player_match_table, "*")
        df_player_champion_mastery = self.sql.get_data(champion_mastery_table, "*")
        df_rune_win_rate = self.sql.get_data(rune_win_table, "*")
        df_rune_pick_rate = self.sql.get_data(rune_pick_table, "*")
        df_champion_stats = self.sql.get_data(champion_stats_table, "*")

        rows_to_update = df_player_match[df_player_match["championLevel"].isnull()]

        data_to_update = []

        for _, row in tqdm(
            rows_to_update.iterrows(), desc="Analise das maestrias dos campeões"
        ):

            puuid = row["puuid"]
            championId = row["championId"]
            perkKeystone = str(row["perkKeystone"])
            perkPrimaryRow1 = str(row["perkPrimaryRow1"])
            perkPrimaryRow2 = str(row["perkPrimaryRow2"])
            perkPrimaryRow3 = str(row["perkPrimaryRow3"])
            perkSecondaryRow1 = str(row["perkSecondaryRow1"])
            perkSecondaryRow2 = str(row["perkSecondaryRow2"])
            individualPosition = row["individualPosition"]

            champion_info = df_player_champion_mastery[
                (df_player_champion_mastery["puuid"] == puuid)
                & (df_player_champion_mastery["championId"] == championId)
            ]

            perk_average_win_rate = (
                df_rune_win_rate[(df_rune_win_rate["championId"] == str(championId))][
                    [
                        perkKeystone,
                        perkPrimaryRow1,
                        perkPrimaryRow2,
                        perkPrimaryRow3,
                        perkSecondaryRow1,
                        perkSecondaryRow2,
                    ]
                ]
                .replace(-1, np.nan)
                .mean(axis=1)
                .iloc[0]
            )

            perk_average_pick_rate = (
                df_rune_pick_rate[(df_rune_pick_rate["championId"] == str(championId))][
                    [
                        perkKeystone,
                        perkPrimaryRow1,
                        perkPrimaryRow2,
                        perkPrimaryRow3,
                        perkSecondaryRow1,
                        perkSecondaryRow2,
                    ]
                ]
                .replace(-1, np.nan)
                .mean(axis=1)
                .iloc[0]
            )

            if np.isnan(perk_average_win_rate):
                perk_average_win_rate = -1.0

            if np.isnan(perk_average_pick_rate):
                perk_average_pick_rate = -1.0

            map_lane = {
                "BOTTOM": "adc",
                "UTILITY": "support",
                "MIDDLE": "mid",
                "TOP": "top",
                "JUNGLE": "jungle",
            }

            if individualPosition != "Invalid":
                champion_win_pick_rate = df_champion_stats[
                    (df_champion_stats["championId"] == str(championId))
                    & (df_champion_stats["lane"] == map_lane[individualPosition])
                ]

                champion_pick_rate = champion_win_pick_rate["pickRate"].iloc[0]
                champion_win_rate = champion_win_pick_rate["winRate"].iloc[0]
            else:
                champion_pick_rate = -1.0
                champion_win_rate = -1.0
            try:
                championLevel = champion_info["championLevel"].iloc[0]
                championPoints = champion_info["championPoints"].iloc[0]
            except Exception as e:
                print(e)
                championLevel = -1.0
                championPoints = -1.0

            data_to_update.append(
                {
                    "puuid": puuid,
                    "matchId": row["matchId"],
                    "championLevel": championLevel,
                    "championPoints": championPoints,
                    "runeWinRate": perk_average_win_rate,
                    "runePickRate": perk_average_pick_rate,
                    "championWinRate": champion_win_rate,
                    "championPickRate": champion_pick_rate,
                }
            )

        df_updates = pd.DataFrame(data_to_update)
        match_columns = ["puuid", "matchId"]

        self.sql.update_data(df_updates, player_match_table, match_columns)

    def create_database(self):
        # Obter dados das tabelas
        matches_data = self.sql.get_data(match_table, "*")
        teams_data = self.sql.get_data(team_table, "*")
        players_matches_data = self.sql.get_data(player_match_table, "*")

        # Selecionar informações do lado azul
        blue_side_teams_data = teams_data[teams_data["teamId"] == 100][
            ["matchId", "win"]
        ]

        # Pivotar métricas que dependem de ambos os lados
        side_metrics = teams_data.pivot(
            index="matchId",
            columns="teamId",
            values=["baronKills", "dragonKills", "riftHeraldKills"],
        )
        side_metrics.columns = [
            f"{'blue_side' if col[1] == 100 else 'red_side'}_{col[0]}"
            for col in side_metrics.columns
        ]

        # Agregar dados de PlayerMatches
        player_aggregated_data = (
            players_matches_data.groupby(["matchId", "teamId"])
            .agg(
                # Média
                avg_summoner_level=("summonerLevel", "mean"),
                avg_kda=("kda", "mean"),
                avg_champion_level=("championLevel", "mean"),
                avg_champion_points=("championPoints", "mean"),
                avg_champion_win_rate=("championWinRate", "mean"),
                avg_champion_pick_rate=("championPickRate", "mean"),
                avg_champ_experience=("champExperience", "mean"),
                avg_rune_win_rate=("runeWinRate", "mean"),
                avg_rune_pick_rate=("runePickRate", "mean"),
                avg_vision_score=("visionScore", "mean"),
                avg_longest_time_spent_living=("longestTimeSpentLiving", "mean"),
                # Soma
                total_kills=("kills", "sum"),
                total_deaths=("deaths", "sum"),
                total_assists=("assists", "sum"),
                total_gold_earned=("goldEarned", "sum"),
                total_consumables_purchased=("consumablesPurchased", "sum"),
                total_all_in_pings=("allInPings", "sum"),
                total_assist_me_pings=("assistMePings", "sum"),
                total_basic_pings=("basicPings", "sum"),
                total_command_pings=("commandPings", "sum"),
                total_danger_pings=("dangerPings", "sum"),
                total_enemy_missing_pings=("enemyMissingPings", "sum"),
                total_enemy_vision_pings=("enemyVisionPings", "sum"),
                total_get_back_pings=("getBackPings", "sum"),
                total_need_vision_pings=("needVisionPings", "sum"),
                total_on_my_way_pings=("onMyWayPings", "sum"),
                total_push_pings=("pushPings", "sum"),
                total_vision_cleared_pings=("visionClearedPings", "sum"),
                total_damage_taken=("totalDamageTaken", "sum"),
                total_damage_dealt_to_champions=("totalDamageDealtToChampions", "sum"),
                total_heal=("totalHeal", "sum"),
                total_time_ccing_others=("timeCCingOthers", "sum"),
                total_minions_killed=("totalMinionsKilled", "sum"),
                total_neutral_minions_killed=("totalNeutralMinionsKilled", "sum"),
                total_time_spent_dead=("totalTimeSpentDead", "sum"),
                total_detector_wards_placed=("detectorWardsPlaced", "sum"),
                total_vision_wards_bought_in_game=("visionWardsBoughtInGame", "sum"),
                total_wards_placed=("wardsPlaced", "sum"),
            )
            .reset_index()
        )

        # Pivotar dados agregados de PlayerMatches por time
        player_metrics_pivot = player_aggregated_data.pivot(
            index="matchId",
            columns="teamId",
            values=[
                "avg_summoner_level",
                "avg_kda",
                "avg_champion_level",
                "avg_champion_points",
                "avg_champion_win_rate",
                "avg_champion_pick_rate",
                "avg_champ_experience",
                "avg_rune_win_rate",
                "avg_rune_pick_rate",
                "avg_vision_score",
                "avg_longest_time_spent_living",
                "total_kills",
                "total_deaths",
                "total_assists",
                "total_gold_earned",
                "total_consumables_purchased",
                "total_all_in_pings",
                "total_assist_me_pings",
                "total_basic_pings",
                "total_command_pings",
                "total_danger_pings",
                "total_enemy_missing_pings",
                "total_enemy_vision_pings",
                "total_get_back_pings",
                "total_need_vision_pings",
                "total_on_my_way_pings",
                "total_push_pings",
                "total_vision_cleared_pings",
                "total_damage_taken",
                "total_damage_dealt_to_champions",
                "total_heal",
                "total_time_ccing_others",
                "total_minions_killed",
                "total_neutral_minions_killed",
                "total_time_spent_dead",
                "total_detector_wards_placed",
                "total_vision_wards_bought_in_game",
                "total_wards_placed",
            ],
        )
        player_metrics_pivot.columns = [
            f"{'blue_side' if col[1] == 100 else 'red_side'}_{col[0]}"
            for col in player_metrics_pivot.columns
        ]

        # Combinar todos os dados em um único DataFrame
        combined_data = matches_data.merge(
            blue_side_teams_data, on="matchId", how="left"
        )
        combined_data = combined_data.merge(side_metrics, on="matchId", how="left")
        combined_data = combined_data.merge(
            player_metrics_pivot, on="matchId", how="left"
        )

        # Identificar e remover duplicatas com base no ID do jogador
        players_matches_data["team_position"] = (
            players_matches_data["teamId"].astype(str)
            + "_"
            + players_matches_data["individualPosition"]
        )
        duplicated_matches = list(
            players_matches_data[
                players_matches_data.duplicated(
                    subset=["matchId", "team_position"], keep=False
                )
            ]["matchId"].unique()
        )

        filtered_players_matches_data = players_matches_data[
            ~players_matches_data["matchId"].isin(duplicated_matches)
        ]

        # Pivotar jogadores para obter a coluna do campeão
        player_champions = filtered_players_matches_data.pivot(
            index="matchId", columns="team_position", values="champion"
        )

        # Preencher valores ausentes com base na posição válida
        for column in player_champions.filter(like="100_").columns:
            if column != "100_Invalid":
                player_champions[column] = player_champions[column].fillna(
                    player_champions["100_Invalid"]
                )
        for column in player_champions.filter(like="200_").columns:
            if column != "200_Invalid":
                player_champions[column] = player_champions[column].fillna(
                    player_champions["200_Invalid"]
                )

        # Remover colunas de "Invalid"
        player_champions = player_champions.drop(columns=["100_Invalid", "200_Invalid"])

        # Adicionar as colunas de jogadores ao DataFrame final
        final_data = combined_data.join(player_champions, on="matchId", how="inner")
        final_data["gameStartDate"] = pd.to_datetime(
            final_data["gameStartTimestamp"], unit="s"
        ).dt.date

        final_data.to_csv(os.path.join(docs_path, "data.csv"), index=False)


if __name__ == "__main__":
    processor = LeagueDataProcessing()
    processor.update_mastery_champions()
    processor.create_database()
