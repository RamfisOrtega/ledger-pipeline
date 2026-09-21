import csv
from dataclasses import asdict, fields
from pathlib import Path
from ledger.model import Transaction, DeadLetterRecord, Record


class Writer:

    @staticmethod
    def write_transactions(transactions: list[Transaction], path: Path | str) -> None:
        column_names = [field.name for field in fields(Transaction)]

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, mode="w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=column_names)
            writer.writeheader()

            for transaction in transactions:
                writer.writerow(asdict(transaction))

    @staticmethod
    def write_dead_letters(dead_letters: list[DeadLetterRecord], path: Path | str) -> None:
        column_names = [field.name for field in fields(Record)] + ["reason"]

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, mode="w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=column_names)
            writer.writeheader()

            for dead_letter in dead_letters:
                row = asdict(dead_letter.raw_record)
                row["reason"] = dead_letter.reason_code.name
                writer.writerow(row)