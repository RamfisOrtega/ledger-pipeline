# ledger-pipeline

A dependency-free Python ETL for a messy transaction ledger. Reads CSV and
JSON, validates every row, and routes bad rows to a dead-letter queue with
reason codes — nothing is dropped silently. Airflow and dbt on Databricks
Free Edition are the planned orchestration and warehouse layers.

```powershell
python main.py
```

No third-party packages. Python 3.12. `pytest` for the tests.

---

## The idea

Most ETL tutorials show you the happy path: read a file, cast the columns,
write a table. Real exports are not like that. A supplier changes a format,
a currency arrives lowercase, an amount arrives as `1,250.00`, and a job
that "succeeded" quietly wrote 40 rows instead of 51.

This pipeline is built around the opposite assumption: **some rows will be
broken, and you need to know which ones and why.**

```
read  ─▶  validate  ─▶  transform  ─▶  summarize
              │
              └─▶  dead letters (kept, with a reason)
```

Every row ends up in exactly one of two places. `total_read` always equals
`valid_count + invalid_count`. If it doesn't, a row vanished — and a row
that vanishes without a trace is the bug this whole design exists to prevent.

---

## Why a dead-letter queue

The obvious way to handle a bad row is to skip it:

```python
for row in rows:
    try:
        transactions.append(to_transaction(row))
    except Exception:
        continue          # ← the bug
```

That job goes green forever. The table shrinks and nobody is paged.

Instead, a rejected row becomes a `DeadLetterRecord`: the original raw
record, untouched, plus the `ReasonCode` that rejected it.

```python
@dataclass
class DeadLetterRecord:
    raw_record: Record
    reason_code: ReasonCode
```

That buys three things:

- **Counts you can alert on.** If `UNPARSEABLE_AMOUNT` goes from 4 to 4000
  overnight, a supplier changed their export. Nobody will email you about it.
- **Replay.** The raw record is intact, so a fixed parser can re-run the
  rejects without re-reading the source.
- **A specific answer.** Not "some rows failed" but "T0028's amount had a
  thousands separator."

---

## Why two record types

```python
@dataclass
class Record:              # raw strings, straight off the file
    amount: str

@dataclass(frozen=True)
class Transaction:         # validated, typed, immutable
    amount: Decimal
```

`Record` is mutable and stringly-typed because that is honestly what a CSV
gives you. `Transaction` is frozen because it is a settled fact — once a row
has been validated, no later code gets to quietly adjust it.

The type system now carries the guarantee. A function taking a `Transaction`
cannot be handed an unvalidated row by accident.

**`Decimal`, not `float`.** `0.1 + 0.2 != 0.3`. Money does not tolerate that.

---

## Why validation is separate from mapping

`TransactionValidator` answers one question per rule and returns a reason, or
`None`. `TransactionMapper` assumes its input is already clean and does
nothing but convert types.

The alternative — one function that validates while it converts — fails
every rule at the first exception, so you learn about one problem per run
instead of all of them.

The cost of the split is that both sides must agree on what "parseable"
means. `Decimal("1,250.00")` raises, so `T0028` is dead-lettered before the
mapper ever sees it. Teach one side a new rule and the other has to learn it
too.

---

## Three traps in the data

The 51 rows in [data/](data/) are deliberately messy. Three lessons are
built into them:

**`0` is not missing.** `0`, `""`, `None` and `[]` are all falsy and none of
them mean the same thing. `if amount:` throws away `T0013` and `T0044` —
real transactions that happen to be zero. The check is
`if amount not in (None, "")`.

**The CSV and the JSON disagree.** Same 51 transactions, two exports:

| | CSV | JSON |
|---|---|---|
| a hole | `""` | `null` → `None` |
| amounts | always text | numbers |
| counterparty | two flat columns | nested `{"name": ..., "country": ...}` |
| blank category | `""` | the key is **absent** |
| tags | cannot express them | a list |

Writing one validator that copes with both is most of the work.

**Fail loudly.** `except Exception: return None` turns a broken job into a
green job with an empty table. Catch the one error you can actually handle.

---

## The data

51 rows, 50 unique IDs — `T0025` is booked twice. March 2026, 5 accounts,
4 currencies, 10 counterparties, 9 categories.

| Row | What's wrong | Caught by |
|---|---|---|
| `T0007`, `T0031` | No amount (`""` / `null`) | `MISSING_OR_NA_AMOUNT` |
| `T0040` | Amount is `N/A` | `MISSING_OR_NA_AMOUNT` |
| `T0028` | Amount is `1,250.00` | `UNPARSEABLE_AMOUNT` |
| `T0025` | Same ID, two dates | `DUPLICATE_TXN_ID` |
| `T0026` | `fx_rate_to_chf` is `0` | `INVALID_ZERO_FX_RATE` |
| `T0011` | `fx_rate_to_chf` is blank | `UNPARSEABLE_FX_RATE` |
| `T0013`, `T0044` | Amount is `0` — **valid, not a hole** | passes |
| `T0021`, `T0038` | Negative amounts — refunds | passes |
| `T0034` | Amount padded: `"  89.90  "` | passes |
| `T0003`, `T0017` | Lowercase currency | passes, normalised |
| `T0009`, `T0023` | Padded counterparty name | passes, stripped |

Roughly 47 of 51 amounts parse with a plain `float()`. That ratio is about
what real data feels like.

---

## Layout

```
ledger/
├── model.py       Record, Transaction, DeadLetterRecord, RunSummary, ReasonCode
├── read.py        CSV and JSON into raw dicts
├── validate.py    one rule per method, returns a ReasonCode or None
├── transform.py   validated Record -> frozen Transaction
└── summarize.py   counts per run, including a tally per reason
tests/             pytest, one file per module
data/              the 51 rows, exported twice
```

---

## Tests

```powershell
pytest
```

The reader tests build tiny files with `tmp_path` rather than leaning on the
real export, plus two smoke tests asserting the real files still have 51 rows
— so a broken export fails a test instead of silently shrinking a table.

---

## Not built yet

`dags/` and `dbt/` are scaffolding for the next phase. They are empty on
purpose.

| Layer | Job |
|---|---|
| `ledger/` | parse, validate, dead-letter — **this is what exists** |
| Airflow | scheduling, retries, task ordering |
| dbt on Databricks Free Edition | joins, aggregates, marts — SQL, not Python |

The Python layer is finished first on purpose: orchestration around a
pipeline that drops rows silently only schedules the problem.
