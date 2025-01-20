import json

import pandas as pd
from tqdm import tqdm

from libs.extract_lib.stats import StatsFetcher
from libs.riot_lib.riot import LeagueOfLegends
from libs.sql_lib.sql import SQLClient
from settings import champion_stats_table, docs_path, rune_pick_table, rune_win_table


class LeagueStatsExtract:
    def __init__(self):
        self.lol = LeagueOfLegends()
        self.sql = SQLClient(use_sqlalchemy=False)
        self.docs_path = docs_path

    def get_json_files(self):
        json_types = [
            ("latest", "champion"),
            ("latest", "item"),
            ("latest", "rune_reforged"),
            ("latest", "language"),
            ("6.24.1", "mastery"),
            ("latest", "profile_icon"),
            ("6.24.1", "rune"),
            ("latest", "summoner_spells"),
            ("latest", "map"),
        ]

        for version, data_type in json_types:
            self.lol.get_data_dragon_json(version=version, data_type=data_type)

    def get_champion_ids(self):
        with open(self.docs_path + "/champion.json", "r", encoding="utf-8") as file:
            champions = json.load(file)
        return [champion_info["key"] for champion_info in champions["data"].values()]

    def get_rune_ids(self):
        with open(
            self.docs_path + "/rune_reforged.json", "r", encoding="utf-8"
        ) as file:
            runes = json.load(file)

        primary_rune_ids = [
            r["id"] for rune in runes for r in rune["slots"][0]["runes"]
        ]
        secondary_rune_ids = [
            r["id"]
            for rune in runes
            for slot in rune["slots"][1:]
            for r in slot["runes"]
        ]
        return primary_rune_ids, secondary_rune_ids

    def get_rune_stats(self):
        champion_ids = self.get_champion_ids()
        primary_rune_ids, secondary_rune_ids = self.get_rune_ids()

        win_rate_stats = {}
        pick_rate_stats = {}

        for champion_id in tqdm(champion_ids, desc="Processando runas dos campeões"):
            stats = StatsFetcher(champion_id)

            win_rate_stats[champion_id] = {}
            pick_rate_stats[champion_id] = {}

            for rune_id in primary_rune_ids + secondary_rune_ids:
                try:
                    win_rate, pick_rate = map(
                        lambda value: float(value.replace("%", "")),
                        (
                            stats.get_rune_stats(rune_id)
                            if rune_id in primary_rune_ids
                            else stats.get_secundary_rune_stats(rune_id)
                        ).values(),
                    )
                except:
                    win_rate, pick_rate = -1.0, -1.0
                finally:
                    win_rate_stats[champion_id][rune_id] = win_rate
                    pick_rate_stats[champion_id][rune_id] = pick_rate

        self._save_to_sql(win_rate_stats, rune_win_table)
        self._save_to_sql(pick_rate_stats, rune_pick_table)

    def get_champion_stats(self):
        champion_ids = self.get_champion_ids()
        lanes = ["top", "jungle", "mid", "adc", "support"]

        champion_stats = []

        for champion_id in tqdm(champion_ids, desc="Processando status dos campeões"):
            stats = StatsFetcher(champion_id)

            for lane in lanes:
                try:
                    win_rate, pick_rate = map(
                        lambda value: float(value.replace("%", "")),
                        stats.get_champion_stats(lane).values(),
                    )
                except:
                    win_rate, pick_rate = -1.0, -1.0
                champion_stats.append(
                    {
                        "championId": champion_id,
                        "lane": lane,
                        "winRate": win_rate,
                        "pickRate": pick_rate,
                    }
                )

        df_champion_stats = pd.DataFrame(champion_stats)
        self.sql.insert_dataframe(
            df_champion_stats, champion_stats_table, ["championId", "lane"]
        )

    def _save_to_sql(self, stats_dict, table_name):
        df_stats = pd.DataFrame.from_dict(stats_dict, orient="index").reset_index()
        df_stats.rename(columns={"index": "championId"}, inplace=True)
        self.sql.insert_dataframe(df_stats, table_name, "championId")


if __name__ == "__main__":
    extract = LeagueStatsExtract()
    extract.get_json_files()

    # Excluir tabelas se existirem
    extract.sql.drop_table(rune_win_table)
    extract.sql.drop_table(rune_pick_table)
    extract.sql.drop_table(champion_stats_table)

    extract.get_rune_stats()
    extract.get_champion_stats()
