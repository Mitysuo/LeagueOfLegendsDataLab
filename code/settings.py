import os
from dotenv import load_dotenv

load_dotenv()

queries_path = os.getenv("QUERY_PATH")

API_KEY = os.getenv("API_KEY")
