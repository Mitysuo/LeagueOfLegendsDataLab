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
GAME_VERSION="14.20"
REGION="BR1"
QUEUE="Ranked" # Não há outras opções

# Configuração SQL
TRUSTED_CONNECTION = os.getenv("TRUSTED_CONNECTION")
USER_SQL = os.getenv("USER_SQL")
PASSWORD_SQL = os.getenv("PASSWORD_SQL")
DRIVER = os.getenv("DRIVER")
SERVER = os.getenv("SERVER")
DATABASE = os.getenv("DATABASE")

# Nome das Tabelas
match_table = os.getenv("MATCH")
player_table = os.getenv("PLAYER")
team_table = os.getenv("TEAM")
player_match_table = os.getenv("PLAYER_MATCH")

# Quantidade de dados a serem extraídos
AMOUNT = os.getenv("AMOUNT")