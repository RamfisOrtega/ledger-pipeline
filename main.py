
import csv
from ledger.read import Reader
from ledger.validate import TransactionValidator
from ledger.transform import TransactionMapper
from ledger.summarize import RunSummarizer
import json
from pathlib import Path
from ledger.model import Record

DATA = Path(__file__).parent / "data"
CSV_PATH = DATA / "transactions.csv"
JSON_PATH = DATA / "transactions.json"

if __name__ == "__main__":

    dead_letters = []
    transactions = []

    # Fetch the data

    rows = Reader.read_csv_rows(CSV_PATH)
    records = [Record(**row) for row in rows]

    # Validate the data: Get the valid records (Transaction) and the invalid ones (DeadLetterRecord)

    validator = TransactionValidator()

    for record in records:
        dead_letter = validator.validate(record)

        if dead_letter is None:
            transaction = TransactionMapper.to_transaction(record)
            transactions.append(transaction)
        else:
            dead_letters.append(dead_letter)


    # Aggreate into a final summary
    summary = RunSummarizer.summarize(str(CSV_PATH), transactions, dead_letters)

    print(f"{summary.source}: {summary.valid_count} valid, {summary.invalid_count} rejected")
    for reason, count in summary.reasons.items():
        print(f"  {count:>3}  {reason.value}")
