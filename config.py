# config.py
from pathlib import Path

ROOT = Path(__file__).parent

DATA = ROOT / "data"
CSV_PATH = DATA / "transactions.csv"
JSON_PATH = DATA / "transactions.json"

OUT = ROOT / "out"
TRANSACTIONS_OUT = OUT / "transactions.csv"
DEAD_LETTERS_OUT = OUT / "dead_letters.csv"