from ledger.model import DeadLetterRecord, ReasonCode, Record, RunSummary, Transaction
from ledger.summarize import RunSummarizer
from datetime import date
from dataclasses import FrozenInstanceError
from decimal import Decimal
import pytest


@pytest.fixture
def source() -> str:
    return "data/transactions.csv"

@pytest.fixture
def valid_transactions() -> list[Transaction]:
    """Three clean valid_transactions, as the mapper hands them over."""
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


@pytest.fixture
def summarizer() -> RunSummarizer:
    return RunSummarizer()


def test_summarize_returns_a_run_summary(summarizer : RunSummarizer,
                                         source: str,
                                         valid_transactions: list[Transaction],
                                        dead_letters: list[DeadLetterRecord]):
    summary = summarizer.summarize(source, valid_transactions, dead_letters)

    assert isinstance(summary, RunSummary)

def test_summarize_keeps_the_source(summarizer : RunSummarizer,
                                    source: str,
                                    valid_transactions: list[Transaction],
                                    dead_letters: list[DeadLetterRecord]):

    summary = summarizer.summarize(source, valid_transactions, dead_letters)

    assert summary.source == "data/transactions.csv"

def test_summarize_counts_the_valid_rows(summarizer : RunSummarizer,
                                        source: str,
                                        valid_transactions: list[Transaction],
                                        dead_letters: list[DeadLetterRecord]):

    summary = summarizer.summarize(source, valid_transactions, dead_letters)

    assert summary.valid_count == 3

def test_summarize_counts_the_invalid_rows(summarizer : RunSummarizer,
                                            source: str,
                                            valid_transactions: list[Transaction],
                                            dead_letters: list[DeadLetterRecord]):

    summary = summarizer.summarize(source, valid_transactions, dead_letters)

    assert summary.invalid_count == 4

def test_summarize_derives_the_total(summarizer : RunSummarizer,
                                    source: str,
                                    valid_transactions: list[Transaction],
                                    dead_letters: list[DeadLetterRecord]):

    summary = summarizer.summarize(source, valid_transactions, dead_letters)

    assert summary.total_read == 7

def test_no_row_is_ever_lost(summarizer : RunSummarizer,
                            source: str,
                            valid_transactions: list[Transaction],
                            dead_letters: list[DeadLetterRecord]):

    summary = summarizer.summarize(source, valid_transactions, dead_letters)

    assert summary.total_read == summary.valid_count + summary.invalid_count

def test_summarize_tallies_each_reason(summarizer : RunSummarizer,
                            source: str,
                            valid_transactions: list[Transaction],
                            dead_letters: list[DeadLetterRecord]):

    summary = summarizer.summarize(source, valid_transactions, dead_letters)

    assert summary.reasons == {
        ReasonCode.MISSING_OR_NA_AMOUNT: 2,
        ReasonCode.UNPARSEABLE_AMOUNT: 1,
        ReasonCode.DUPLICATE_TXN_ID: 1,
    }

def test_summarize_omits_reasons_that_did_not_happen(summarizer : RunSummarizer,
                            source: str,
                            valid_transactions: list[Transaction],
                            dead_letters: list[DeadLetterRecord]):

    summary = summarizer.summarize(source, valid_transactions, dead_letters)

    assert ReasonCode.INVALID_ZERO_FX_RATE not in summary.reasons

def test_a_clean_run_has_no_reasons(summarizer : RunSummarizer,
                            source: str,
                            valid_transactions: list[Transaction]):

    summary = summarizer.summarize(source, valid_transactions, [])

    assert summary.invalid_count == 0
    assert summary.reasons == {}
    assert summary.total_read == 3

def test_a_run_that_rejected_everything(summarizer : RunSummarizer,
                            source: str,
                            dead_letters: list[DeadLetterRecord]):

    summary = summarizer.summarize(source, [], dead_letters)

    assert summary.valid_count == 0
    assert summary.total_read == 4

def test_an_empty_run(summarizer : RunSummarizer,
                            source: str):
    """An empty source file is not an error, it is a run that read nothing."""
    summary = summarizer.summarize(source, [], [])

    assert summary.total_read == 0
    assert summary.reasons == {}

def test_summary_is_immutable(summarizer : RunSummarizer,
                            source: str,
                            valid_transactions: list[Transaction],
                            dead_letters: list[DeadLetterRecord]):

    summary = summarizer.summarize(source, valid_transactions, dead_letters)

    with pytest.raises(FrozenInstanceError):
        summary.valid_count = 99
