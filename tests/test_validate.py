import pytest
from ledger.model import DeadLetterRecord, ReasonCode, Record
from ledger.validate import TransactionValidator

@pytest.fixture
def validator() -> TransactionValidator:
    return TransactionValidator()

@pytest.fixture
def valid_raw_records() -> list[dict]:
    return [
        {
            "txn_id": "T0001",
            "booked_at": "2026-03-01",
            "account": "A1",
            "counterparty": "Helvetia Payroll AG",
            "counterparty_country": "CH",
            "category": "payroll",
            "amount": "45.00",
            "currency": "CHF",
            "fx_rate_to_chf": "1.0",
            "status": "booked"
        },
        {
            "txn_id": "T0002",
            "booked_at": "2026-03-02",
            "account": "A3",
            "counterparty": "Zurich Office Rent GmbH",
            "counterparty_country": "CH",
            "category": "tax",
            "amount": "182.53",
            "currency": "GBP",
            "fx_rate_to_chf": "1.12",
            "status": "booked"
        },
    ]

def test_validate_fails_when_txn_id_is_empty(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_raw_record = valid_raw_records[0]
    valid_raw_record["txn_id"] = ""
    rut = Record(**valid_raw_record)

    result = validator.validate(rut)

    assert isinstance(result, DeadLetterRecord)
    assert result.reason_code == ReasonCode.MISSING_TXN_ID

def test_validate_duplicate_txn_id_exist(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_raw_records[1]["txn_id"] = "T0001"


    rst_list = [validator.validate(Record(**r)) for r in valid_raw_records]
    assert rst_list[0] is None
    assert rst_list[1].reason_code == ReasonCode.DUPLICATE_TXN_ID


@pytest.mark.parametrize(
    "amount",
    ["", "   ", "N/A", " N/A ", "n/a"],
    ids=["empty", "whitespace", "na", "padded_na", "lowercase_na"],
)

def test_validate_amount_is_blank_or_na(validator: TransactionValidator, valid_raw_records: list[dict], amount: str):
    valid_raw_record = valid_raw_records[0]
    valid_raw_record["amount"] = amount

    result = validator.validate(Record(**valid_raw_record))

    assert isinstance(result, DeadLetterRecord)
    assert result.reason_code == ReasonCode.MISSING_OR_NA_AMOUNT


def test_validate_accepts_a_zero_amount(validator: TransactionValidator, valid_raw_records: list[dict]):
    """Zero is a legitimate booked amount, not a missing one."""
    valid_raw_record = valid_raw_records[0]
    valid_raw_record["amount"] = "0.00"

    assert validator.validate(Record(**valid_raw_record)) is None


def test_validate_fail_to_unparseable_thousands_separator_amount(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_raw_record = valid_raw_records[0]
    valid_raw_record["amount"]="1,250.00"

    rut= Record(**valid_raw_record)

    result = validator.validate(rut)
    assert result.reason_code == ReasonCode.UNPARSEABLE_AMOUNT

def test_validate_fail_to_unparseable_european_decimal_comma_amount(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_record = valid_raw_records[0]
    valid_record["amount"]="45,00"

    rut=Record(**valid_record)

    result = validator.validate(rut)
    assert result.reason_code == ReasonCode.UNPARSEABLE_AMOUNT


def test_validate_fail_to_garbage_amount(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_record=valid_raw_records[0]
    valid_record["amount"]="abc"

    rut=Record(**valid_record)

    result=validator.validate(rut)
    assert result.reason_code == ReasonCode.UNPARSEABLE_AMOUNT

def test_validate_fail_to_currency_prefix_amount(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_record=valid_raw_records[0]
    valid_record["amount"]="CHF 45.00"

    rut=Record(**valid_record)

    result=validator.validate(rut)
    assert result.reason_code == ReasonCode.UNPARSEABLE_AMOUNT


def test_validate_fail_to_accounting_negative_amount(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_record=valid_raw_records[0]
    valid_record["amount"]="(45.00)"

    rut=Record(**valid_record)

    result=validator.validate(rut)
    assert result.reason_code == ReasonCode.UNPARSEABLE_AMOUNT

def test_validate_fail_to_nan_amount(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_record=valid_raw_records[0]
    valid_record["amount"]="NaN"

    rut=Record(**valid_record)

    result=validator.validate(rut)
    assert result.reason_code == ReasonCode.UNPARSEABLE_AMOUNT

def test_validate_fail_to_inf_amount(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_record=valid_raw_records[0]
    valid_record["amount"]="inf"

    rut=Record(**valid_record)

    result=validator.validate(rut)
    assert result.reason_code == ReasonCode.UNPARSEABLE_AMOUNT

def test_validate_fail_to_invalid_zero_fx_rate(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_raw_record=valid_raw_records[0]
    valid_raw_record["fx_rate_to_chf"]="0.0"

    rut=Record(**valid_raw_record)

    result = validator.validate(rut)

    assert result.reason_code== ReasonCode.INVALID_ZERO_FX_RATE

def test_validate_fail_unparseable_currency_name_fx_rate(validator: TransactionValidator, valid_raw_records: list[list]):
    valid_raw_record=valid_raw_records[0]
    valid_raw_record["fx_rate_to_chf"]="EUR"

    rut=Record(**valid_raw_record)
    result=validator.validate(rut)

    assert result.reason_code==ReasonCode.UNPARSEABLE_FX_RATE

def test_validate_zero_fx_rate_rule_ignores_unparseable_rate(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_raw_record = valid_raw_records[0]
    valid_raw_record["fx_rate_to_chf"] = "EUR"

    rut = Record(**valid_raw_record)

    result = validator._is_invalid_zero_fx_rate(rut)
    assert result is False

@pytest.mark.parametrize(
        "booked_at",
         ["01/03/2026", "2026-13-01", "2026-02-30", "", "not-a-date"],
        ids=["slash_format", "month_13", "feb_30", "empty", "garbage"],
)

def test_validate_invalid_date_format_fail(validator: TransactionValidator, valid_raw_records: list[dict], booked_at: str):
    valid_raw_record=valid_raw_records[0]
    valid_raw_record["booked_at"]= booked_at

    rut=Record(**valid_raw_record)
    result= validator.validate(rut)

    assert result.reason_code== ReasonCode.INVALID_DATE_FORMAT

@pytest.mark.parametrize(
        "fx_rate_to_chf",
         ["NaN", "nan", "inf", "-inf", "Infinity"],
        ids=["nan", "lowercase_nan", "inf", "negative_inf", "infinity"],
)

def test_validate_fail_to_non_finite_fx_rate(validator: TransactionValidator, valid_raw_records: list[dict], fx_rate_to_chf: str):
    valid_raw_record=valid_raw_records[0]
    valid_raw_record["fx_rate_to_chf"]= fx_rate_to_chf

    rut=Record(**valid_raw_record)
    result= validator.validate(rut)

    assert result.reason_code== ReasonCode.UNPARSEABLE_FX_RATE

# HAPPY PATH TESTS
# A rule that flagged everything would pass every test above.

def test_validate_accepts_a_negative_amount(validator: TransactionValidator, valid_raw_records: list[dict]):

    valid_raw_record=valid_raw_records[0]
    valid_raw_record["amount"]="-45.00"

    rut=Record(**valid_raw_record)
    result= validator.validate(rut)

    assert result is None

def test_validate_accepts_a_padded_amount(validator: TransactionValidator, valid_raw_records: list[dict]):

    valid_raw_record=valid_raw_records[0]
    valid_raw_record["amount"]=" 45.00 "

    rut=Record(**valid_raw_record)
    result= validator.validate(rut)

    assert result is None

def test_validate_accepts_a_valid_date(validator: TransactionValidator, valid_raw_records: list[dict]):
    valid_raw_record=valid_raw_records[0]
    valid_raw_record["booked_at"]="2026-03-01"

    rut=Record(**valid_raw_record)
    result= validator.validate(rut)

    assert result is None

def test_validate_accepts_a_fully_clean_record(validator: TransactionValidator, valid_raw_records: list[dict]):
    rut=Record(**valid_raw_records[0])

    assert validator.validate(rut) is None
