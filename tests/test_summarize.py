from ledger.model import DeadLetterRecord, ReasonCode, RunSummary, Transaction
from ledger.summarize import RunSummarizer
from dataclasses import FrozenInstanceError
import pytest


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
