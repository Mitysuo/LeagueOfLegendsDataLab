import os
import sys
from riotwatcher import LolWatcher, ApiError
import requests
import pandas as pd
import json
from tqdm import tqdm
import time

sys.path.append(os.path.abspath(os.path.join(__file__, "../..")))
from sql_lib.sql import SQLClient
sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))
from settings import docs_path, API_KEY

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

        for summonerId in tqdm(summonerIds, desc="Obtendo PUUIDs"):
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
        chall_df['tier'] = 'CHALLENGER'

        gm_df, m_df = pd.DataFrame(), pd.DataFrame()

        # Recuperar dados para o tier Grandmaster se top > 300
        if top > len(chall_df):
            grandmaster_league = self.watcher.league.grandmaster_by_queue(self.region, self.queue)
            gm_df = pd.DataFrame(grandmaster_league['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)
            gm_df['tier'] = 'GRANDMASTER'

        # Recuperar dados para o tier Master se top > 1000
        if top > len(gm_df):
            master_league = self.watcher.league.masters_by_queue(self.region, self.queue)
            m_df = pd.DataFrame(master_league['entries']).sort_values('leaguePoints', ascending=False).reset_index(drop=True)
            m_df['tier'] = 'MASTER'

        # Concatenar os DataFrames e selecionar os X melhores jogadores
        df = pd.concat([chall_df, gm_df, m_df]).reset_index(drop=True)[:top]

        # Incluir riot_id e riot_tag se especificado
        if include_tag:
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
        index_error = 0
        try:
            match_json = self.watcher.match.by_id(self.region, match_id)
        except Exception as _:
            time.sleep(20)
            index_error += 1

            if index_error >= 2:
                return False, False, False
            return self.get_match(match_id)  # Tenta novamente

        metadata = match_json['metadata']
        info = match_json['info']
        participants = metadata["participants"]
        matchId = metadata["matchId"]

        ### Team information
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

        picks = []
        for index in range(2):
            # Champions Picks
            championPickTurn = [info['participants'][r + index*5]['championId'] for r in range(5)]
            picks.append(championPickTurn)

            team_data = {
                # Initial information
                "matchId": matchId,
                "teamId" : teams[index]["teamId"],
                "win" : teams[index]["win"],

                # Pick and ban information
                "championPickTurn1" : championPickTurn[0],
                "championPickTurn2" : championPickTurn[1],
                "championPickTurn3" : championPickTurn[2],
                "championPickTurn4" : championPickTurn[3],
                "championPickTurn5" : championPickTurn[4],
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

        ### Match information
        gameStartTimestamp = info['gameStartTimestamp']
        gameEndTimestamp = info['gameEndTimestamp']

        match_data = {
            "matchId" : matchId,
            "participants" : json.dumps(participants),
            "endOfGameResult" : info['endOfGameResult'],
            "timePlayed" : (gameEndTimestamp-gameStartTimestamp)/1000,
            "gameVersion" : info['gameVersion'],
            "gameEndedInSurrender" : info["participants"][0]["gameEndedInSurrender"],
            "gameEndedInEarlySurrender" : info["participants"][0]["gameEndedInEarlySurrender"],
            "gameStartTimestamp" : gameStartTimestamp/1000
        }

        df_match = pd.DataFrame([match_data])
            
        ### Player information
        player_list = []

        for index, participant in enumerate(participants):
            player = info['participants'][index]
            perks = player['perks']
            challenges = player['challenges']
            summonerId = player["summonerId"]

            # Runes
            primaryRune = [perks['styles'][0]['selections'][i]['perk'] for i in range(4)]
            secudaryRune = [perks['styles'][1]['selections'][i]['perk'] for i in range(2)]

            # Extra Information
            rank = self.get_player_rank(summonerId)
            tierRank = rank['tier'][0] + ' ' + rank['rank'][0] if rank is not None else "Missing"

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
                "summonnerId" : summonerId,
                "summonerLevel" : player["summonerLevel"],
                "individualPosition": player['individualPosition'],
                "teamPosition" : player["teamPosition"],
                "kills" : player['kills'],
                "deaths" : player['deaths'],
                "assists" : player['assists'],
                "kda" : challenges['kda'],
                "win" : player['win'],
                "tierRank" : tierRank,

                # Champion information
                "champion" : player['championName'],
                "championId" : player['championId'],
                "champLevel" : player['champLevel'],
                "champExperience" : player["champExperience"],

                # Perks information
                "perkKeystone" : primaryRune[0],
                "perkPrimaryRow1" : primaryRune[1],
                "perkPrimaryRow2" : primaryRune[2],
                "perkPrimaryRow3" : primaryRune[3],
                "perkPrimaryStyle" : perks['styles'][0]['style'],
                "perkSecondaryRow1" : secudaryRune[0],
                "perkSecondaryRow2" : secudaryRune[1],
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
            mastery_champions = self.watcher.champion_mastery.by_puuid(self.region, puuid)
            
            grade_mapping = {
                "S+": 12, "S": 11, "S-": 10,
                "A+": 9, "A": 8, "A-": 7,
                "B+": 6, "B": 5, "B-": 4,
                "C+": 3, "C": 2, "C-": 1,
                "D": 0
            }   

            mastery_list = []
            for champion in mastery_champions:
                
                reverse_mapping = {v: k for k, v in grade_mapping.items()}
                grades = champion.get("milestoneGrades", "Missing")
                
                if grades != "Missing":
                    numeric_grades = [grade_mapping.get(grade) for grade in grades if grade in grade_mapping]
                    if not numeric_grades:
                        grades = "Missing"
                    else:
                        num_average = sum(numeric_grades) / len(numeric_grades)
                        grades = reverse_mapping[round(num_average)]
                
                mastery_data = {
                    "puuid" : champion["puuid"],
                    "championId" : champion["championId"],
                    "championLevel" : champion["championLevel"],
                    "championPoints" : champion["championPoints"],
                    "lastPlayTime" : champion["lastPlayTime"]/1000,
                    "averageGrade" : grades
                }

                mastery_list.append(mastery_data)
            df_mastery_champion = pd.DataFrame(mastery_list)
            return df_mastery_champion
        
        except ApiError as err:
            if err.response.status_code == 429:
                print("Limite de requisições atingido. Tente novamente mais tarde.")
            elif err.response.status_code == 404:
                print(f"SummonerId não encontrado.")
            else:
                print(f"Ocorreu um erro: {err}")
    
    def get_player_rank(self, summonerId):
        try:
            all_rank = self.watcher.league.by_summoner(self.region, summonerId)

            if len(all_rank) == 0:
                return None
            
            player_rank = None

            for index, rank in enumerate(all_rank):
                index += 1
                if rank['queueType'] == 'RANKED_SOLO_5x5':
                    player_rank = rank
                    break

                if index == len(all_rank):
                    return None

            rank_dict = {
                'leagueId' : player_rank['leagueId'],
                'queueType' : player_rank['queueType'],
                'tier' : player_rank['tier'],
                'rank' : player_rank['rank'],
                'leaguePoints' : player_rank['leaguePoints'],
                'wins' : player_rank['wins'],
                'losses' : player_rank['losses'],
                'veteran' : player_rank['veteran'],
                'inactive' : player_rank['inactive'],
                'freshBlood' : player_rank['freshBlood'],
                'hotStreak' : player_rank['hotStreak']
            }

            df_rank = pd.DataFrame([rank_dict])
            
            return df_rank
        except Exception as e:
            print(e)
        
    def get_data_dragon_json(self, version='latest', data_type='champion'):
        """
        Obtém os arquivos JSON do Data Dragon da Riot Games usando o RiotWatcher e os salva na pasta especificada em docs_path.
        
        :param version: Versão do Data Dragon a ser baixada (ex.: '13.19.1'). Use 'latest' para a versão mais recente.
        :param data_type: Tipo de dados a serem baixados (ex.: 'champion', 'item', 'rune').
        :return: Caminho completo do arquivo JSON salvo.
        """
        # Se a versão for 'latest', busca a versão mais recente diretamente da API do Data Dragon
        if version == 'latest':
            versions = self.watcher.data_dragon.versions_all()
            version = versions[0]

        # Baixa o JSON específico usando o RiotWatcher
        match data_type:
            case 'champion':
                data = self.watcher.data_dragon.champions(version)
            case 'item':
                data = self.watcher.data_dragon.items(version)
            case 'rune_reforged':
                data = self.watcher.data_dragon.runes_reforged(version)
            case 'language':
                data = self.watcher.data_dragon.languages(version)
            case 'mastery':
                data = self.watcher.data_dragon.masteries(version)
            case 'profile_icon':
                data = self.watcher.data_dragon.profile_icons(version)
            case 'rune':
                data = self.watcher.data_dragon.runes(version)
            case 'summoner_spells':
                data = self.watcher.data_dragon.summoner_spells(version)
            case 'map':
                data = self.watcher.data_dragon.maps(version)
            case _:
                raise ValueError(f"Tipo de dado '{data_type}' não suportado.")

        # Cria a pasta se ela não existir
        os.makedirs(docs_path, exist_ok=True)

        # Caminho completo onde o arquivo será salvo
        file_path = os.path.join(docs_path, f"{data_type}.json")

        # Salva o JSON no arquivo
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        
if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    lol_data = LeagueOfLegends(queue='420') # RANKED_SOLO_5x5 or 420
    # df = lol_data.get_league(2000)

    match_ids = lol_data.get_matchlist('yibS_oarcTPUlOdhwnSVnah_BiIvGRZP4_fpi_HiJ0Sny1yDnCGzWPyQKariiPj3QVOye8HEOENyZA', count=3)
    print(type(match_ids))


    # df_mastery = lol_data.get_mastery_champion('45vQt28hMXEfGOBx3eqywuUXTBb1UzFMbqsEmpkaUn_I93kcU9KAple9kGlC3Fni7RO0RG_NBRiq5Q')
    # print(df_mastery['averageGrade'])
    # print(df_mastery.info())

    # df_rank = lol_data.get_player_rank("gsWcPbFY8bcnEOcxjJL4wwkQV2n_HbdJQMRYTHYvvP_hdKo")
    # print(df_rank)

    # lol_data.get_data_dragon_json(version='latest', data_type='profile_icon')