from collections import Counter
from ledger.model import DeadLetterRecord, RunSummary, Transaction

class RunSummarizer:

    @staticmethod
    def summarize(source: str, transactions: list[Transaction], dead_letters: list[DeadLetterRecord]) -> RunSummary:
        return RunSummary(
            source= source,
            total_read= len(transactions) + len(dead_letters),
            valid_count= len(transactions),
            invalid_count= len(dead_letters),
            reasons=Counter(r.reason_code for r in dead_letters)
        )