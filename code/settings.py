import os
from dotenv import load_dotenv

load_dotenv()

# Paths
queries_path = os.getenv("QUERY_PATH")
docs_path = os.getenv("DOCS_PATH")

# Variables
API_KEY = os.getenv("API_KEY")
