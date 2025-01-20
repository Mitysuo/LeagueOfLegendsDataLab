import os

from dotenv import load_dotenv

load_dotenv()

# Pastas
queries_path = os.getenv("QUERY_PATH")
docs_path = os.getenv("DOCS_PATH")
logs_path = os.getenv("LOGS_PATH")

# Riot API
API_KEY = os.getenv("API_KEY")

# Parâmetros LOL
GAME_VERSION = "14.20"
REGION = "BR1"
QUEUE = "Ranked"  # Não há outras opções

# Configuração SQL
TRUSTED_CONNECTION = os.getenv("TRUSTED_CONNECTION")
USER_SQL = os.getenv("USER_SQL")
PASSWORD_SQL = os.getenv("PASSWORD_SQL")
DRIVER = os.getenv("DRIVER")
SERVER = os.getenv("SERVER")
DATABASE = os.getenv("DATABASE")

# Nome das Tabelas
match_table = os.getenv("MATCH_TABLE")
player_table = os.getenv("PLAYER_TABLE")
team_table = os.getenv("TEAM_TABLE")
player_match_table = os.getenv("PLAYER_MATCH_TABLE")
rune_win_table = os.getenv("RUNE_WIN_TABLE")
rune_pick_table = os.getenv("RUNE_PICK_TABLE")
champion_stats_table = os.getenv("CHAMPION_STATS_TABLE")
champion_mastery_table = os.getenv("CHAMPION_MASTERY_TABLE")

# Quantidade de dados a serem extraídos
AMOUNT = os.getenv("AMOUNT")
