import os
import sys
from riotwatcher import LolWatcher, ApiError
import pandas as pd
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

        # Get advanced information
        for index in range(5):
            if info['participants'][index]["firstTowerKill"]:
                firstTower = [True, False]
            elif index == 4:
                firstTower = [False, True]

            if info['participants'][index]["firstBloodKill"]:
                firstKill = [True, False]
            elif index == 4:
                firstKill = [False, True]

        for index in range(2):
            team_data = {
                # Initial information
                "matchId": matchId,
                "teamId" : teams[index]["teamId"],
                "win" : teams[index]["win"],

                # Pick and ban information
                "championPickTurn1" : info['participants'][0 + index*5]['championId'],
                "championPickTurn2" : info['participants'][1 + index*5]['championId'],
                "championPickTurn3" : info['participants'][2 + index*5]['championId'],
                "championPickTurn4" : info['participants'][3 + index*5]['championId'],
                "championPickTurn5" : info['participants'][4 + index*5]['championId'],
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
                "towerKills" : teams[index]["objectives"]["tower"]["kills"],

                # Advanced information
                "firstTower" : firstTower[index],
                "firstKill" : firstKill[index]
            }

            team_list.append(team_data)

        df_team = pd.DataFrame(team_list)
            
        # Player information
        player_list = []

        for index, participant in enumerate(participants):
            player = info['participants'][index]
            perks = player['perks']
            challenges = player['challenges']

            if index < 5:
                teamId = teams[0]["teamId"]
            else:
                teamId = teams[1]["teamId"]

            player_data = {
                # Player information
                "puuid" : participant,
                "matchId": matchId,
                "teamId": teamId,
                "participantId": player['participantId'],
                "summonnerId" : player["summonerId"],
                "summonerLevel" : player["summonerLevel"],
                "individualPosition": player['individualPosition'],
                "teamPosition" : player["teamPosition"],
                "kills" : player['kills'],
                "deaths" : player['deaths'],
                "assists" : player['assists'],
                "kda" : challenges['kda'],

                # Champion information
                "champion" : player['championName'],
                "championId" : player['championId'],
                "champLevel" : player['champLevel'],
                "champExperience" : player["champExperience"],

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
                "assistMePings" : player['assistMePings'],
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
                "magicDamageDealtToChampions" : player["magicDamageDealtToChampions"],
                "magicDamageTaken" : player["magicDamageTaken"],
                "physicalDamageDealt" : player["physicalDamageDealt"],
                "physicalDamageDealtToChampions" : player["physicalDamageDealtToChampions"],
                "physicalDamageTaken" : player["physicalDamageTaken"],
                "totalDamageDealt" : player["totalDamageDealt"],
                "totalDamageDealtToChampions" : player["totalDamageDealtToChampions"],
                "totalDamageTaken" : player["totalDamageTaken"],
                "totalDamageShieldedOnTeammates" : player["totalDamageShieldedOnTeammates"],
                "totalHeal" : player["totalHeal"],
                "totalHealsOnTeammates" : player["totalHealsOnTeammates"],
                "totalUnitsHealed" : player["totalUnitsHealed"],
                "timeCCingOthers" : player["timeCCingOthers"],
                "totalTimeCCDealt" : player["totalTimeCCDealt"],
                "totalTimeSpentDead" : player["totalTimeSpentDead"],
                "trueDamageDealt" : player["trueDamageDealt"],
                "trueDamageDealtToChampions" : player["trueDamageDealtToChampions"],
                "trueDamageTaken" : player["trueDamageTaken"],
                "firstBloodKill" : player["firstBloodKill"],
                "firstTowerKill" : player["firstTowerKill"],
                "doubleKills" : player["doubleKills"],
                "tripleKills" : player["tripleKills"],
                "quadraKills" : player["quadraKills"],
                "pentaKills" : player["pentaKills"],

                # Objectives information
                "totalMinionsKilled" : player['totalMinionsKilled'],
                "totalNeutralMinionsKilled" : player['totalAllyJungleMinionsKilled'] + player['totalEnemyJungleMinionsKilled'],

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
                "wardsKilled" : player["wardsKilled"],

                # Advanced Statistics information
                "damagePerMinute" : challenges["damagePerMinute"],
                "damageTakenOnTeamPercentage" : challenges["damageTakenOnTeamPercentage"],
                "goldPerMinute" : challenges["goldPerMinute"],
                "visionScorePerMinute" : challenges["visionScorePerMinute"],
                "longestTimeSpentLiving" : player["longestTimeSpentLiving"]
            }

            player_list.append(player_data)

        df_player = pd.DataFrame(player_list)

        return df_match, df_team, df_player
    
    def get_mastery_champion(self, puuid):
        try:
            mastery = self.watcher.champion_mastery.by_puuid(self.region, puuid)

            return mastery
        
        except ApiError as err:
            if err.response.status_code == 429:
                print("Limite de requisições atingido. Tente novamente mais tarde.")
            elif err.response.status_code == 404:
                print(f"SummonerId não encontrado.")
            else:
                print(f"Ocorreu um erro: {err}")
    
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    lol_data = LeagueOfLegends()
    # df = lol_data.get_league(2000)
    # print(df)

    mastery = lol_data.get_mastery_champion('_1jFGvcCNhrsG8tn9rK3faM5W4wHtGJY_AMjT8uXarv6XoNFfg8FgrzAC8E1glBLBZNF_PFditkaGg')

    print(mastery)

