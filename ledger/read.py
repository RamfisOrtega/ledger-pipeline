import csv
import json
from pathlib import Path

class Reader:
    """A standard utility class for reading multiple data extraction formats."""

    @staticmethod
    def read_csv_rows(path: Path | str) -> list[dict]:
        """Reads a CSV file and converts it directly into a list of raw string dictionaries."""
        with open(path, mode="r", encoding="utf-8", newline="") as csv_file:
            # DictReader uses the first line of the file automatically as dict keys
            return list(csv.DictReader(csv_file))

    @staticmethod
    def read_json_rows(path: Path | str) -> list[dict]:
        """Reads a structured JSON file directly into native lists/dictionaries."""
        with open(path, mode="r", encoding="utf-8") as json_file:
            return json.load(json_file)
