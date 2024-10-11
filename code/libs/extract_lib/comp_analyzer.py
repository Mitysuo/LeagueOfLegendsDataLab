from playwright.sync_api import sync_playwright

class LolTheoryScraper:
    def __init__(self):
        self.url = "https://loltheory.gg/lol/team-comp-analyzer/solo-queue?user-role=middle&rank-range=diamond_plus&recommendation-method=classic"
    
    def __start_browser(self):
        self.playwright = sync_playwright().start()
        # Alterar para headless=False para exibir o navegador
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()

    def __close_browser(self):
        self.browser.close()
        self.playwright.stop()

    def get_stats(self, champions):
        self.__start_browser()
        self.page.goto(self.url)

        # Encontra todos os SVGs que representam os slots de campeões
        svg_elements = self.page.query_selector_all('svg.add-champ.add-fav-icon')

        # Itera sobre cada SVG e seleciona um campeão da lista
        for i, svg_element in enumerate(svg_elements):
            if i >= len(champions):
                break

            # Clica no SVG atual
            svg_element.click()

            # Aguarda a lista de campeões aparecer e clica no campeão especificado
            self.page.wait_for_selector(f'span.name:text("{champions[i]}")')
            self.page.click(f'span.name:text("{champions[i]}")')

        # Obtém as informações desejadas
        risk_value = self.page.text_content('span.risk.font-weight-600.font-number')
        win_rate_value = self.page.text_content('span.champion-column.win-rate.font-number')

        self.__close_browser()

        return {
            "Risk Value:": float(risk_value.strip()),
            "Win Rate:": win_rate_value.strip()
        }

# Uso da classe:
if __name__ == "__main__":
    # Lista de campeões para serem selecionados
    champions_to_select = ["Aatrox", "Amumu", "Elise", "Ashe", "Blitzcrank", "Caitlyn", "Darius", "Draven", "Ekko", "Alistar"]
    
    scraper = LolTheoryScraper()
    risk_value, win_rate = scraper.get_stats(champions_to_select).values()

    print(f'Risk Value: {risk_value}')
    print(f'Win Rate: {win_rate}')
