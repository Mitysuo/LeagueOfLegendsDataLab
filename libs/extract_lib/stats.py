import json

import requests
from bs4 import BeautifulSoup


class StatsFetcher:

    def __init__(self, champion_id) -> None:
        self.champion_id = champion_id
        self.champion_name = self.__get_champion_name()

    def __get_champion_name(self):
        with open("code/docs/champion.json", "r", encoding="utf-8") as file:
            data = json.load(file)

        for _, details in data["data"].items():
            if details["key"] == str(self.champion_id):
                return details["name"]
        return None

    def get_rune_stats(self, rune_id):
        # URL do campeão com base no ID
        url = f"https://leagueofitems.com/champions/{self.champion_id}"

        # Fazendo a requisição HTTP para o site
        response = requests.get(url)

        # Verificando se a requisição foi bem-sucedida
        if response.status_code != 200:
            raise Exception(
                f"Failed to load page with status code: {response.status_code}"
            )

        # Parsing do conteúdo HTML da página
        soup = BeautifulSoup(response.text, "html.parser")

        # Procurando a div que contém as informações das runas
        runes_div = soup.find(
            "div", class_="flex w-full space-x-2 overflow-x-auto pb-2"
        )

        if not runes_div:
            raise Exception("Couldn't find the runes container div.")

        # Procurando a runa específica pelo ID
        rune_link = runes_div.find("a", href=f"/runes/{rune_id}")

        if not rune_link:
            raise Exception(f"Couldn't find the rune with ID {rune_id}.")

        # Extraindo as estatísticas de winRate e pickRate
        winRate = rune_link.find_all("p")[1].text.strip()
        pickRate = rune_link.find_all("p")[3].text.strip()

        return {"winRate": winRate, "pickRate": pickRate}

    def get_secundary_rune_stats(self, secundary_rune_id):
        # URL do campeão com base no ID
        url = f"https://leagueofitems.com/champions/{self.champion_id}"

        # Fazendo a requisição HTTP para o site
        response = requests.get(url)

        # Verificando se a requisição foi bem-sucedida
        if response.status_code != 200:
            raise Exception(
                f"Failed to load page with status code: {response.status_code}"
            )

        # Parsing do conteúdo HTML da página
        soup = BeautifulSoup(response.text, "html.parser")

        # Procurando a div que contém as informações das runas
        runes_div = soup.find_all(
            "div", class_="flex w-full space-x-2 overflow-x-auto pb-2"
        )

        if not runes_div:
            raise Exception("Couldn't find the runes container div.")

        if len(runes_div) >= 2:
            secondary_rune = runes_div[1]
        else:
            raise Exception("Couldn't find the secondary rune div.")

        # Procurando a runa específica pelo ID
        secondary_rune_link = secondary_rune.find(
            "a", href=f"/runes/{secundary_rune_id}"
        )

        if not secondary_rune_link:
            raise Exception(
                f"Couldn't find the secondary rune with ID {secundary_rune_id}."
            )

        # Extraindo as estatísticas de winRate e pickRate
        winRate = secondary_rune_link.find_all("p")[1].text.strip()
        pickRate = secondary_rune_link.find_all("p")[3].text.strip()

        return {"winRate": winRate, "pickRate": pickRate}

    def get_champion_stats(self, lane):
        # URL do campeão com base no ID e lane
        url = f"https://www.op.gg/champions/{self.champion_name}/build/{lane}?region=br&tier=diamond_plus&type=ranked"

        # Fazendo a requisição HTTP para o site
        response = requests.get(url)

        # Verificando se a requisição foi bem-sucedida
        if response.status_code != 200:
            raise Exception(
                f"Failed to load page with status code: {response.status_code}"
            )

        # Parsing do conteúdo HTML da página
        soup = BeautifulSoup(response.text, "html.parser")

        # Encontrar os contêineres de win rate e pick rate
        rate_containers = soup.find_all("div", class_="rate-container")

        # Extrair o valor de win rate
        winRate = rate_containers[0].find("strong").text

        # Extrair o valor de pick rate
        pickRate = rate_containers[1].find("strong").text

        return {"winRate": winRate, "pickRate": pickRate}


# Exemplo de uso
if __name__ == "__main__":
    champion_id = 266  # Artrox
    rune_id = 8473
    fetcher = StatsFetcher(champion_id)
    winRate, pickRate = fetcher.get_secundary_rune_stats(rune_id).values()
    print(winRate)
    print(pickRate)

    winRate, pickRate = fetcher.get_champion_stats("top").values()
    print(winRate)
    print(pickRate)
