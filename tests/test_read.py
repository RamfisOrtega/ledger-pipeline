from ledger.read import Reader
from pathlib import Path
import json
import pytest

DATA = Path(__file__).parent.parent / "data"
CSV_PATH = DATA / "transactions.csv"
JSON_PATH = DATA / "transactions.json"


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    """A two-row CSV: one full row, one with a blank amount."""
    path = tmp_path / "transactions.csv"
    path.write_text(
        "txn_id,category,amount\n"
        "T0001,payroll,45.00\n"
        "T0007,payroll,\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def json_file(tmp_path: Path) -> Path:
    """The same two rows as the JSON export writes them."""
    path = tmp_path / "transactions.json"
    path.write_text(
        json.dumps(
            [
                {
                    "txn_id": "T0001",
                    "counterparty": {"name": "Helvetia Payroll AG", "country": "CH"},
                    "category": "payroll",
                    "amount": 45.0,
                    "tags": ["recurring"],
                },
                {
                    "txn_id": "T0019",
                    "counterparty": {"name": "Nordwind Logistics BV", "country": "NL"},
                    "amount": None,
                    "tags": [],
                },
            ]
        ),
        encoding="utf-8",
    )
    return path


# --- CSV ---------------------------------------------------------------

def test_read_csv_rows_returns_a_dict_per_row(csv_file: Path):
    rows = Reader.read_csv_rows(csv_file)

    assert len(rows) == 2
    assert rows[0] == {"txn_id": "T0001", "category": "payroll", "amount": "45.00"}


def test_read_csv_rows_uses_the_header_as_keys(csv_file: Path):
    rows = Reader.read_csv_rows(csv_file)

    assert list(rows[0].keys()) == ["txn_id", "category", "amount"]


def test_read_csv_rows_gives_an_empty_string_for_a_hole(csv_file: Path):
    rows = Reader.read_csv_rows(csv_file)

    assert rows[1]["amount"] == ""


def test_read_csv_rows_keeps_every_value_as_text(csv_file: Path):
    rows = Reader.read_csv_rows(csv_file)

    assert all(isinstance(value, str) for value in rows[0].values())


def test_read_csv_rows_raises_when_the_file_is_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        Reader.read_csv_rows(tmp_path / "nope.csv")


# --- JSON --------------------------------------------------------------

def test_read_json_rows_returns_a_dict_per_row(json_file: Path):
    rows = Reader.read_json_rows(json_file)

    assert len(rows) == 2
    assert rows[0]["txn_id"] == "T0001"


def test_read_json_rows_gives_none_for_a_hole(json_file: Path):
    rows = Reader.read_json_rows(json_file)

    assert rows[1]["amount"] is None


def test_read_json_rows_keeps_amounts_as_numbers(json_file: Path):
    rows = Reader.read_json_rows(json_file)

    assert rows[0]["amount"] == 45.0
    assert not isinstance(rows[0]["amount"], str)


def test_read_json_rows_keeps_the_counterparty_nested(json_file: Path):
    rows = Reader.read_json_rows(json_file)

    assert rows[0]["counterparty"] == {"name": "Helvetia Payroll AG", "country": "CH"}


def test_read_json_rows_omits_the_key_when_a_category_is_blank(json_file: Path):
    rows = Reader.read_json_rows(json_file)

    assert "category" not in rows[1]


def test_read_json_rows_keeps_tags_as_a_list(json_file: Path):
    rows = Reader.read_json_rows(json_file)

    assert rows[0]["tags"] == ["recurring"]


def test_read_json_rows_raises_when_the_file_is_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        Reader.read_json_rows(tmp_path / "nope.json")


# --- the real exports --------------------------------------------------

def test_the_real_csv_still_has_51_rows():
    assert len(Reader.read_csv_rows(CSV_PATH)) == 51


def test_the_real_json_still_has_51_rows():
    assert len(Reader.read_json_rows(JSON_PATH)) == 51
