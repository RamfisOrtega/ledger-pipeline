
from ledger.model import DeadLetterRecord, Record, ReasonCode
from decimal import Decimal, InvalidOperation
import math
from datetime import datetime

class TransactionValidator:

    def __init__(self) -> None:
        self._seen_txn_ids: set[str] = set()

    @staticmethod
    def _has_txn_id(record: Record) -> bool:
        return bool(record.txn_id and not record.txn_id.isspace())

    def _has_duplicate_txn_id(self, record: Record) -> bool:
        if record.txn_id in self._seen_txn_ids:
            return True

        self._seen_txn_ids.add(record.txn_id)
        return False

    @staticmethod
    def _is_invalid_amount(record: Record) -> bool:
        amount = record.amount.strip()
        if not amount:
            return True
        if amount.upper() == "N/A":
            return True
        return False

    @staticmethod
    def _is_unparseable_amount(record) -> bool:
        try:
            amount = Decimal(record.amount)
        except InvalidOperation:
            return True
        
        return amount.is_infinite() or amount.is_nan()

    @staticmethod
    def _is_invalid_zero_fx_rate(record: Record) -> bool:
        """Unparseable rates are not this rule's business, so they are left to pass."""
        try:
            rate = float(record.fx_rate_to_chf)
        except ValueError:
            return False

        return rate == 0.0

    @staticmethod
    def _is_unparseable_fx_rate(record) -> bool:
        try:
            rate = float(record.fx_rate_to_chf)
        except ValueError:
            return True

        return not math.isfinite(rate)

    @staticmethod
    def _is_invalid_date_format(record) ->bool:
        try:
            datetime.strptime(record.booked_at, "%Y-%m-%d")

        except ValueError:
            return True

        return False
    
    def validate(self,record: Record) -> DeadLetterRecord | None:    

        if not self._has_txn_id(record):
            return DeadLetterRecord(record, ReasonCode.MISSING_TXN_ID)

        if self._has_duplicate_txn_id(record):
            return DeadLetterRecord(record, ReasonCode.DUPLICATE_TXN_ID)

        if self._is_invalid_amount(record):
            return DeadLetterRecord(record, ReasonCode.MISSING_OR_NA_AMOUNT)

        if self._is_unparseable_amount(record):
            return DeadLetterRecord(record, ReasonCode.UNPARSEABLE_AMOUNT)

        if self._is_unparseable_fx_rate(record):
            return DeadLetterRecord(record, ReasonCode.UNPARSEABLE_FX_RATE)

        if self._is_invalid_zero_fx_rate(record):
            return DeadLetterRecord(record, ReasonCode.INVALID_ZERO_FX_RATE)

        if self._is_invalid_date_format(record):
            return DeadLetterRecord(record,ReasonCode.INVALID_DATE_FORMAT)

        return None