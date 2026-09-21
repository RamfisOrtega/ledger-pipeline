from ledger.model import Record, Transaction
from ledger.transform import TransactionMapper
from datetime import datetime, date
from decimal import Decimal
import pytest


@pytest.fixture
def valid_record() -> Record:
    return Record(
        txn_id="T0001",
        booked_at="2026-03-01",
        account="A1",
        counterparty="  Helvetia Payroll AG  ",
        counterparty_country="CH",
        category="payroll",
        amount="45.00",
        currency="chf",
        fx_rate_to_chf="1.0",
        status="booked",
    )

@pytest.fixture
def mapper() -> TransactionMapper:
    return TransactionMapper()


def test_returns_a_transaction(mapper: TransactionMapper, valid_record: Record):
    rut = mapper.to_transaction(valid_record)

    assert isinstance(rut, Transaction)


def test_booked_at_becomes_a_date(mapper: TransactionMapper, valid_record: Record):
    rut = mapper.to_transaction(valid_record)

    assert rut.booked_at == date(2026, 3, 1)


def test_amount_becomes_a_decimal(mapper: TransactionMapper, valid_record: Record):
    rut = mapper.to_transaction(valid_record)

    assert isinstance(rut.amount, Decimal)
    assert rut.amount == Decimal("45.00")


def test_fx_rate_becomes_a_float(mapper: TransactionMapper, valid_record: Record):
    rut = mapper.to_transaction(valid_record)

    assert isinstance(rut.fx_rate_to_chf, float)
    assert rut.fx_rate_to_chf == 1.0


def test_counterparty_is_stripped(mapper: TransactionMapper, valid_record: Record):
    rut = mapper.to_transaction(valid_record)

    assert rut.counterparty == "Helvetia Payroll AG"


def test_currency_is_uppercased(mapper: TransactionMapper, valid_record: Record):
    rut = mapper.to_transaction(valid_record)

    assert rut.currency == "CHF"


def test_plain_fields_pass_through(mapper: TransactionMapper, valid_record: Record):
    rut = mapper.to_transaction(valid_record)

    assert rut.txn_id == "T0001"
    assert rut.account == "A1"
    assert rut.counterparty_country == "CH"
    assert rut.category == "payroll"
    assert rut.status == "booked"


def test_zero_amount_is_kept(mapper, valid_record):
    valid_record.amount = "0.00"
    assert mapper.to_transaction(valid_record).amount == Decimal("0.00")


def test_negative_amount_is_kept(mapper, valid_record):
    valid_record.amount = "-120.50"
    assert mapper.to_transaction(valid_record).amount == Decimal("-120.50")


def test_padded_amount_is_parsed(mapper, valid_record):
    valid_record.amount = "  89.90  "
    assert mapper.to_transaction(valid_record).amount == Decimal("89.90")

def test_source_record_is_unchanged(mapper, valid_record):
    mapper.to_transaction(valid_record)
    assert valid_record.currency == "chf"
