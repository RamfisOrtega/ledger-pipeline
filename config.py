# config.py
from pathlib import Path

ROOT = Path(__file__).parent

DATA = ROOT / "data"
CSV_PATH = DATA / "transactions.csv"
JSON_PATH = DATA / "transactions.json"

SEEDS = ROOT / "dbt" / "seeds"
TRANSACTIONS_OUT = SEEDS / "transactions.csv"
DEAD_LETTERS_OUT = SEEDS / "dead_letters.csv"
