import os
from dotenv import load_dotenv

load_dotenv()

# Paths
queries_path = os.getenv("QUERY_PATH")
docs_path = os.getenv("DOCS_PATH")
logs_path = os.getenv("LOGS_PATH")

# Variables
API_KEY = os.getenv("API_KEY")
TRUSTED_CONNECTION = os.getenv("TRUSTED_CONNECTION")
USER_SQL = os.getenv("USER_SQL")
PASSWORD_SQL = os.getenv("PASSWORD_SQL")
DRIVER = os.getenv("DRIVER")
SERVER = os.getenv("SERVER")
DATABASE = os.getenv("DATABASE")