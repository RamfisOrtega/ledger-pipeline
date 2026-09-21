from ledger.model import Record, Transaction
from datetime import datetime
from decimal import Decimal

class TransactionMapper:

    @staticmethod
    def _get_booked_at(record_date: str) -> datetime:
        return datetime.strptime(record_date, "%Y-%m-%d").date()

    @staticmethod
    def to_transaction(record: Record) -> Transaction:
        return Transaction(

            txn_id=record.txn_id,
            booked_at=TransactionMapper._get_booked_at(record.booked_at),
            account=record.account,
            counterparty=record.counterparty.strip(),
            counterparty_country=record.counterparty_country,
            category=record.category,
            amount=Decimal(record.amount),
            currency=record.currency.upper(),
            fx_rate_to_chf=float(record.fx_rate_to_chf),
            status=record.status,
            
        )
