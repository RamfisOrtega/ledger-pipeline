"""Fixtures shared by every test file in this folder.

pytest loads conftest.py automatically, so nothing imports it.
"""

from ledger.model import DeadLetterRecord, ReasonCode, Record, Transaction
from datetime import date
from decimal import Decimal
import pytest


@pytest.fixture
def source() -> str:
    return "data/transactions.csv"

@pytest.fixture
def valid_transactions() -> list[Transaction]:
    """Three clean transactions, as the mapper hands them over."""
    return [
        Transaction(
            txn_id="T0001",
            booked_at=date(2026, 3, 1),
            account="A1",
            counterparty="Helvetia Payroll AG",
            counterparty_country="CH",
            category="payroll",
            amount=Decimal("45.00"),
            currency="CHF",
            fx_rate_to_chf=1.0,
            status="booked",
        ),
        Transaction(
            txn_id="T0002",
            booked_at=date(2026, 3, 2),
            account="A3",
            counterparty="Zurich Office Rent GmbH",
            counterparty_country="CH",
            category="rent",
            amount=Decimal("182.53"),
            currency="GBP",
            fx_rate_to_chf=1.12,
            status="booked",
        ),
        Transaction(
            txn_id="T0021",
            booked_at=date(2026, 3, 14),
            account="A2",
            counterparty="Nordwind Logistics BV",
            counterparty_country="NL",
            category="refund",
            amount=Decimal("-120.50"),
            currency="EUR",
            fx_rate_to_chf=0.94,
            status="booked",
        ),
    ]

@pytest.fixture
def dead_letters() -> list[DeadLetterRecord]:
    """Four rejects: two share a reason, two are on their own."""
    return [
        DeadLetterRecord(
            Record(
                txn_id="T0007",
                booked_at="2026-03-05",
                account="A1",
                counterparty="Helvetia Payroll AG",
                counterparty_country="CH",
                category="payroll",
                amount="",
                currency="CHF",
                fx_rate_to_chf="1.0",
                status="booked",
            ),
            ReasonCode.MISSING_OR_NA_AMOUNT,
        ),
        DeadLetterRecord(
            Record(
                txn_id="T0040",
                booked_at="2026-03-22",
                account="A4",
                counterparty="Britannia Supplies Ltd",
                counterparty_country="GB",
                category="supplies",
                amount="N/A",
                currency="GBP",
                fx_rate_to_chf="1.12",
                status="pending",
            ),
            ReasonCode.MISSING_OR_NA_AMOUNT,
        ),
        DeadLetterRecord(
            Record(
                txn_id="T0028",
                booked_at="2026-03-17",
                account="A2",
                counterparty="Milano Energia SpA",
                counterparty_country="IT",
                category="energy",
                amount="1,250.00",
                currency="EUR",
                fx_rate_to_chf="0.94",
                status="booked",
            ),
            ReasonCode.UNPARSEABLE_AMOUNT,
        ),
        DeadLetterRecord(
            Record(
                txn_id="T0025",
                booked_at="2026-03-16",
                account="A5",
                counterparty="Atlantic Freight Inc",
                counterparty_country="US",
                category="logistics",
                amount="310.00",
                currency="USD",
                fx_rate_to_chf="0.88",
                status="booked",
            ),
            ReasonCode.DUPLICATE_TXN_ID,
        ),
    ]
