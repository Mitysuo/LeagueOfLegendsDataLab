import os
import sys
from riotwatcher import LolWatcher, ApiError
import pandas as pd
import json

sys.path.append(os.path.abspath(os.path.join(os.getcwd(), '..')))
from settings import API_KEY

class LeagueOfLegends:

    def __init__(self, region='BR1', queue=420):
        self.region = region
        self.queue = queue
        self.watcher = LolWatcher(API_KEY)

    def get_puuid(self, df):
        """Obtém o puuid a partir de um DataFrame com summonerId.

        Args:
            df (DataFrame): DataFrame com a coluna summonerId.

        Returns:
            DataFrame: DataFrame com as colunas summonerId e puuid.
        """
        
        summonerIds = df['summonerId'].tolist()
        puuids = []
        summonerIds_list = []

        for i, summonerId in enumerate(summonerIds):
            if i % 100 == 0:
                print(f'Processing puuids: {i/len(summonerIds)*100:.2f}%')
            try:
                summoner = self.watcher.summoner.by_id(self.region, summonerId)
                puuids.append(summoner['puuid'])
                summonerIds_list.append(summonerId)
            except ApiError as err:
                print(f"Erro ao obter PUUID para summonerId {summonerId}: {err}")

        return pd.DataFrame({'summonerId': summonerIds_list, 'puuid': puuids})

    def get_league(self, top=300, include_tag=True):
        """Obtém os X melhores jogadores em soloq.

        Args:
            top (int, optional): Número de jogadores a retornar. Padrão é 300.
            include_tag (bool, optional): Se deve incluir riot_id e riot_tag. Adiciona tempo de processamento extra. Padrão é True.

        Returns:
            DataFrame: Retorna um DataFrame com os X melhores jogadores em soloq.
        """
        
        # Recuperar dados para o tier Challenger
        challenger_league = self.watcher.league.challenger_by_queue(self.region, self.queue)
        chall_df = pd.DataFrame(challenger_league['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)

        gm_df, m_df = pd.DataFrame(), pd.DataFrame()

        # Recuperar dados para o tier Grandmaster se top > 300
        if top > len(chall_df):
            grandmaster_league = self.watcher.league.grandmaster_by_queue(self.region, self.queue)
            gm_df = pd.DataFrame(grandmaster_league['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)

        # Recuperar dados para o tier Master se top > 1000
        if top > len(gm_df):
            master_league = self.watcher.league.masters_by_queue(self.region, self.queue)
            m_df = pd.DataFrame(master_league['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)

        # Concatenar os DataFrames e selecionar os X melhores jogadores
        df = pd.concat([chall_df, gm_df, m_df]).reset_index(drop=True)[:top]

        # Incluir riot_id e riot_tag se especificado
        if include_tag:
            print('Obtendo PUUIDs . . .')
            puuid_df = self.get_puuid(df)
            df = df.merge(puuid_df, on='summonerId', how='outer')

            # Reordenar colunas
            cols = ['puuid', 'summonerId', 'leaguePoints', 'tier', 'wins', 'losses', 'veteran', 'inactive', 'freshBlood', 'hotStreak']
            df = df[cols].reset_index(drop=True)
            df['rank'] = df.index + 1

        else:
            df = df.reset_index(drop=True)
            df['rank'] = df.index + 1
            cols = ['rank', 'summonerId', 'leaguePoints', 'tier', 'wins', 'losses', 'veteran', 'inactive', 'freshBlood', 'hotStreak']
            df = df[cols]

        return df

    def get_matchlist(self, puuid=None, count=100):
        """
        Obtém os IDs do histórico de partidas para um determinado PUUID.

        Returns:
            List[strings]: Lista do histórico de partidas para um determinado PUUID.
        """
        if not puuid:
            print("PUUID é necessário.")
            return False

        try:
            match_ids = self.watcher.match.matchlist_by_puuid(region=self.region, puuid=puuid, queue=self.queue, count=count)
            return match_ids
        except ApiError as e:
            print(f"Erro ao obter IDs do histórico de partidas: {e}")
            return False
    
    def get_match(self, match_id):
        """
        Obtém dados de uma partida específica.
        """

        try:
            match_json = self.watcher.match.by_id(self.region, match_id)
        except ApiError as e:
            print(f"Erro ao obter dados de partidas: {e}")

        metadata = match_json['metadata']
        info = match_json['info']
        participants = metadata["participants"]

        # Match information
        matchId = metadata["matchId"]
        gameStartTimestamp = info['gameStartTimestamp']
        gameEndTimestamp = info['gameEndTimestamp']
        gameVersion = info['gameVersion']

        if gameVersion[0:5] != '14.16':
            return False

        match_data = {
            "matchId" : matchId,
            "participants" : json.dumps(participants),
            "endOfGameResult" : info['endOfGameResult'],
            "gameStartTimestamp" : gameStartTimestamp,
            "gameEndTimestamp" : gameEndTimestamp,
            "timePlayed" : (gameEndTimestamp-gameStartTimestamp)/1000,
            "gameVersion" : gameVersion,
            "gameEndedInSurrender" : info["participants"][0]["gameEndedInSurrender"],
            "gameEndedInEarlySurrender" : info["participants"][0]["gameEndedInEarlySurrender"]
        }

        df_match = pd.DataFrame([match_data])

        # Team information
        team_list = []

        teams = info['teams']
        teamId = teams[index]["teamId"]
        for index in range(2):
            team_data = {
                # Initial information
                "matchId": matchId,
                "teamId" : teamId,
                "win" : teams[index]["win"],

                # Pick and ban information
                "championBanPickTurn1" : teams[index]["bans"][0]["championId"],
                "championBanPickTurn2" : teams[index]["bans"][1]["championId"],
                "championBanPickTurn3" : teams[index]["bans"][2]["championId"],
                "championBanPickTurn4" : teams[index]["bans"][3]["championId"],
                "championBanPickTurn5" : teams[index]["bans"][4]["championId"],
                
                # Objectives information
                "baronKills" : teams[index]["objectives"]["baron"]["kills"],
                "dragonKills" : teams[index]["objectives"]["dragon"]["kills"],
                "championKills" : teams[index]["objectives"]["champion"]["kills"],
                "inhibitorKills" : teams[index]["objectives"]["inhibitor"]["kills"],
                "riftHeraldKills" : teams[index]["objectives"]["riftHerald"]["kills"],
                "towerKills" : teams[index]["objectives"]["tower"]["kills"]
            }

            team_list.append(team_data)

        df_team = pd.DataFrame(team_list)
            
        # Player information
        for index, participant in enumerate(participants):
            player = info['participants'][index]
            perks = player['perks']
            challenges = player['challenges']

            player_data = {
                # Player information
                "puuid" : participant,
                "matchId": matchId,
                "teamId": teamId,
                "participantId": player['participantId'],
                "summonnerId" : player["summonerId"],
                "summonerLevel" : player["summonerLevel"],
                "individualPosition": player['individualPosition'],
                "lane" : player['lane'],
                "role" : player['role'],
                "teamPosition" : player["teamPosition"],
                "kills" : player['kills'],
                "deaths" : player['deaths'],
                "assists" : player['assists'],
                "kda" : challenges['kda'],

                # Champion information
                "champion" : player['championName'],
                "championId" : player['championId'],
                "championLevel" : player['championLevel'],
                "championTransform" : player['championTransform'],
                "championExperience" : player["championExperience"],

                # Perks information
                "perkKeystone" : perks['styles'][0]['selections'][0]['perk'],
                "perkPrimaryRow1" : perks['styles'][0]['selections'][1]['perk'],
                "perkPrimaryRow2" : perks['styles'][0]['selections'][2]['perk'],
                "perkPrimaryRow3" : perks['styles'][0]['selections'][3]['perk'],
                "perkPrimaryStyle" : perks['styles'][0]['style'],
                "perkSecondaryRow1" : perks['styles'][1]['selections'][0]['perk'],
                "perkSecondaryRow2" : perks['styles'][1]['selections'][1]['perk'],
                "perkSecondaryStyle" : perks['styles'][1]['style'],
                "perkShardDefense" : perks['statPerks']['defense'],
                "perkShardFlex" : perks['statPerks']['flex'],
                "perkShardOffense" : perks['statPerks']['offense'],

                # Itens information
                "item0" : player['item0'],
                "item1" : player['item1'],
                "item2" : player['item2'],
                "item3" : player['item3'],
                "item4" : player['item4'],
                "item5" : player['item5'],
                "item6" : player['item6'],
                "itemsPurchased" : player['itemsPurchased'],
                "consumablesPurchased" : player['consumablesPurchased'],
                "goldEarned" : player['goldEarned'],
                "goldSpent" : player['goldSpent'],

                # Pings information
                "allInPings" : player['allInPings'],
                "assistMePings" : player['AssistMePings'],
                "basicPings" : player['basicPings'],
                "commandPings" : player['commandPings'],
                "dangerPings" : player['dangerPings'],
                "enemyMissingPings" : player['enemyMissingPings'],
                "enemyVisionPings" : player['enemyVisionPings'],
                "getBackPings" : player["getBackPings"],
                "needVisionPings" : player["needVisionPings"],
                "onMyWayPings" : player["onMyWayPings"],
                "pushPings" : player["pushPings"],
                "visionClearedPings" : player["visionClearedPings"],

                # Player performance information
                "damageDealtToBuildings" : player["damageDealtToBuildings"],
                "damageDealtToObjectives" : player["damageDealtToObjectives"],
                "damageDealtToTurrets" : player["damageDealtToTurrets"],
                "damageSelfMitigated" : player["damageSelfMitigated"],
                "magicDamageDealt" : player["magicDamageDealt"],
                "magicDamageDealtToChampions" : player["magicDamageDealToChampions"],
                "magicDamageTaken" : player["magicDamageTaken"],
                "physicalDamageDealt" : player["physicalDamageDealt"],
                "physicalDamageDealtToChampions" : player["physicalDamageDealtToChampions"],
                "physicalDamageTaken" : player["physicalDamageTaken"],
                "totalDamageDealt" : player["totalDamageDeal"],
                "totalDamageDealtToChampions" : player["totalDamageDealtToChampions"],
                "totalDamageTaken" : player["totalDamageTaken"],
                "totalDamageShieldedOnTeammates" : player["totalDamageShieldedOnTeammates"],
                "totalHeal" : player["totalHeal"],
                "totalHealsOnTeammates" : player["totalHealsOnTeammates"],
                "totalUnitsHealed" : player["totalUnitsHealed"],
                "totalTimeCCDealt" : player["totalTimeCCDealt"],
                "totalTimeSpentDead" : player["totalTimeSpentDead"],
                "trueDamageDealt" : player["trueDamageDealt"],
                "trueDamageDealtToChampions" : player["trueDamageDealtToChampions"],
                "trueDamageTaken" : player["trueDamageTaken"],
                "firstBlood" : player["firstBlood"],
                "firstTowerKill" : player["firstTowerKill"],
                "doublekills" : player["doublekills"],
                "trippleKills" : player["tripleKills"],
                "quadraKills" : player["quadraKills"],
                "pentaKills" : player["pentaKills"],

                # Objectives information
                "dragonKills" : player["dragonKills"],
                "inhibitorKills" : player["inhibitorKills"],
                "nexusKills" : player["nexusKills"],
                "turretKills" : player["turretKills"],
                "objectivesStolen" : player["objectivesStolen"],
                "totalMinionsKilled" : player['totalMinionsKilled'],
                "totalNeutralMinionsKilled" : player['totalAllyJungleMinionsKilled'] + player['totalEnemyJungleMinionsKilled'],

                # Advanced Statistics information
                "longestTimeSpentLiving" : player["longestTimeSpentLiving"],

                # Ability information
                "spell1Casts" : player["spell1Casts"],
                "spell2Casts" : player["spell2Casts"],
                "spell3Casts" : player["spell3Casts"],
                "spell4Casts" : player["spell4Casts"],

                # Vision Information
                "sightWardsBoughtInGame" : player["sightWardsBoughtInGame"],
                "detectorWardsPlaced" : player["detectorWardsPlaced"],
                "visionScore" : player["visionScore"],
                "visionClearedPings" : player["visionClearedPings"],
                "visionWardsBoughtInGame" : player["visionWardsBoughtInGame"],
                "wardsPlaced" : player["wardsPlaced"],
                "wardsKilled" : player["wardsKilled"]
            }

if __name__ == "__main__":
    lol_data = LeagueOfLegends()
    df = lol_data.get_league(2000)
    print(df)
