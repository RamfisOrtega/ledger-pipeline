
from ledger.read import Reader
from ledger.validate import TransactionValidator
from ledger.transform import TransactionMapper
from ledger.summarize import RunSummarizer
from ledger.write import Writer
from ledger.model import Record
import logging
from config import CSV_PATH, TRANSACTIONS_OUT, DEAD_LETTERS_OUT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":

    dead_letters = []
    transactions = []
    

    # Fetch the data

    rows = Reader.read_csv_rows(CSV_PATH)
    records = [Record(**row) for row in rows]

    # Validate the data: Get the valid records (Transaction) and the invalid ones (DeadLetterRecord)

    validator = TransactionValidator()

    for record in records:
        dead_letter = validator.validate(record)

        if dead_letter is None:
            transaction = TransactionMapper.to_transaction(record)
            transactions.append(transaction)
        else:
            dead_letters.append(dead_letter)


    # Aggregate into a final summary
    summary = RunSummarizer.summarize(str(CSV_PATH), transactions, dead_letters)
    Writer.write_transactions(transactions, TRANSACTIONS_OUT)
    Writer.write_dead_letters(dead_letters, DEAD_LETTERS_OUT)

    logger.info(
        "%s: %d valid, %d rejected",
        summary.source, summary.valid_count, summary.invalid_count,
    )
    
    for reason, count in summary.reasons.items():
        logger.warning("%3d  %s", count, reason.value)
