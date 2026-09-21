from dataclasses import dataclass
from decimal import Decimal
from datetime import date, datetime
from enum import Enum


class ReasonCode(Enum):
    MISSING_TXN_ID = "Missing primary key (txn_id)"
    DUPLICATE_TXN_ID = "Duplicate transaction ID detected"
    INVALID_DATE_FORMAT = "Date format must be YYYY-MM-DD"
    MISSING_OR_NA_AMOUNT = "Amount is blank or marked N/A"
    UNPARSEABLE_AMOUNT = "Amount cannot be cast to Decimal"
    INVALID_ZERO_FX_RATE = "FX rate cannot be exactly 0.0"
    UNPARSEABLE_FX_RATE = "FX rate cannot be cast to float"


@dataclass
class Record:
    """Represents raw, unvalidated string data directly from the source."""
    txn_id: str
    booked_at: str
    account: str
    counterparty: str
    counterparty_country: str
    category: str
    amount: str
    currency: str
    fx_rate_to_chf: str
    status: str

@dataclass(frozen=True)
class Transaction:
    """Represents a 100% clean, validated transaction record."""
    txn_id: str
    booked_at: date
    account: str
    counterparty: str
    counterparty_country: str
    category: str
    amount: Decimal  # Prevents floating-point rounding issues
    currency: str
    fx_rate_to_chf: float
    status: str

@dataclass
class DeadLetterRecord:
    """Represents a corrupt record captured with its audit context."""
    raw_record: Record
    reason_code: ReasonCode


@dataclass(frozen=True)
class RunSummary:
    """Counts for one pipeline run."""
    source: str           # which file this run read
    total_read: int
    valid_count: int
    invalid_count: int
    reasons: dict[ReasonCode, int]   # how many of each failure
