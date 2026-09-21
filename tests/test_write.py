from ledger.write import Writer
from ledger.read import Reader
from pathlib import Path
import pytest

def test_writes_a_header_row(tmp_path: Path, valid_transactions):
    out_path = tmp_path / "transactions.csv"

    Writer.write_transactions(valid_transactions, out_path)

    fist_line = out_path.read_text(encoding="utf-8").splitlines()[0]
    assert fist_line.split(",") == [
    "txn_id",
    "booked_at",
    "account",
    "counterparty",
    "counterparty_country",
    "category",
    "amount",
    "currency",
    "fx_rate_to_chf",
    "status",
    ]

def test_writes_one_row_per_transaction(tmp_path: Path, valid_transactions):
    out_path = tmp_path / "transactions.csv"

    Writer.write_transactions(valid_transactions, out_path)

    lines = out_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 4


def test_amount_is_written_as_plain_text(tmp_path: Path, valid_transactions):
    out_path = tmp_path / "transactions.csv"

    Writer.write_transactions(valid_transactions, out_path)
    rows = Reader.read_csv_rows(out_path)

    assert rows[0]["amount"] == "45.00"
    assert rows[2]["amount"] == "-120.50"


def test_date_is_written_as_iso(tmp_path: Path, valid_transactions):
    out_path = tmp_path / "transactions.csv"

    Writer.write_transactions(valid_transactions, out_path)
    rows = Reader.read_csv_rows(out_path)

    assert rows[0]["booked_at"] == "2026-03-01"


def test_transactions_round_trip(tmp_path: Path, valid_transactions):
    out_path = tmp_path / "transactions.csv"

    Writer.write_transactions(valid_transactions, out_path)
    rows = Reader.read_csv_rows(out_path)

    assert len(rows) == 3
    assert rows[0]["txn_id"] == "T0001"
    assert rows[0]["counterparty"] == "Helvetia Payroll AG"
    assert rows[0]["currency"] == "CHF"


def test_writing_an_empty_list_still_writes_a_header(tmp_path: Path):
    out_path = tmp_path / "transactions.csv"

    Writer.write_transactions([], out_path)
    lines = out_path.read_text(encoding="utf-8").splitlines()

    assert len(lines) == 1
    assert lines[0].startswith("txn_id,")


def test_creates_the_parent_directory(tmp_path: Path, valid_transactions):
    out_path = tmp_path / "out" / "transactions.csv"

    Writer.write_transactions(valid_transactions, out_path)
    assert out_path.exists()


def test_dead_letters_are_flattened(tmp_path: Path, dead_letters):
    out_path = tmp_path / "dead_letters.csv"

    Writer.write_dead_letters(dead_letters, out_path)
    first_line = out_path.read_text(encoding="utf-8").splitlines()[0]

    assert first_line.split(",") == [
        "txn_id",
        "booked_at",
        "account",
        "counterparty",
        "counterparty_country",
        "category",
        "amount",
        "currency",
        "fx_rate_to_chf",
        "status",
        "reason",
    ]


def test_dead_letter_reason_is_readable(tmp_path: Path, dead_letters):
    out_path = tmp_path / "dead_letters.csv"

    Writer.write_dead_letters(dead_letters, out_path)
    rows = Reader.read_csv_rows(out_path)

    assert rows[0]["reason"] == "MISSING_OR_NA_AMOUNT"
    assert rows[2]["reason"] == "UNPARSEABLE_AMOUNT"


def test_dead_letters_round_trip(tmp_path: Path, dead_letters):
    """A reject can be read back intact, which is what makes replay possible."""
    out_path = tmp_path / "dead_letters.csv"

    Writer.write_dead_letters(dead_letters, out_path)
    rows = Reader.read_csv_rows(out_path)

    assert len(rows) == 4
    assert rows[0]["txn_id"] == "T0007"
    assert rows[0]["amount"] == ""
    assert rows[2]["amount"] == "1,250.00"
