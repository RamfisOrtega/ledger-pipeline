# ledger-pipeline

An end-to-end ETL over a deliberately messy transaction ledger. Dependency-free
Python reads a CSV export, validates every row and routes bad rows to a
dead-letter queue with reason codes — nothing is dropped silently. dbt models
the results on Databricks, and Airflow runs the four steps in order.

```
main.py  ──▶  dbt seed  ──▶  dbt run  ──▶  dbt test
```

| Layer | Does | Depends on |
|---|---|---|
| `ledger/` | parse, validate, dead-letter, summarise | nothing but the standard library |
| `dbt/` | staging views, a monthly spend mart, 6 data tests | dbt-databricks |
| `dags/` | one DAG, four tasks, daily | Airflow 3 via the Astro CLI |

Run the Python layer on its own with no setup at all:

```powershell
python main.py
```

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

**The same data exports two different ways.** [data/](data/) holds the 51
transactions twice — once as CSV, once as JSON — and they disagree on almost
everything:

| | CSV | JSON |
|---|---|---|
| a hole | `""` | `null` → `None` |
| amounts | always text | numbers |
| counterparty | two flat columns | nested `{"name": ..., "country": ...}` |
| blank category | `""` | the key is **absent** |
| tags | cannot express them | a list |

Only the CSV path is wired up today. Feeding the JSON through the same
validator needs a normaliser in front of `Record` — see *Not built yet* below.

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
├── read.py        CSV and JSON into raw dicts (only CSV is wired up)
├── validate.py    one rule per method, returns a ReasonCode or None
├── transform.py   validated Record -> frozen Transaction
├── summarize.py   counts per run, including a tally per reason
└── write.py       results out as CSV, for the warehouse to pick up
dbt/models/
├── staging/       stg_transactions, stg_dead_letters, schema.yml
└── marts/         fct_monthly_spend
dags/
└── ledger_dag.py  the four tasks, in order
config.py          every path in one place
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

## The warehouse layer

`main.py` writes its two result files straight into `dbt/seeds/`, so no human
copies anything between steps. dbt loads them and builds three models:

| Model | Materialised as | Why |
|---|---|---|
| `stg_transactions` | view | casts `amount` to decimal, `booked_at` to date |
| `stg_dead_letters` | view | **casts nothing** — see below |
| `fct_monthly_spend` | table | booked spend per counterparty per month, in CHF |

**Staging rejects stay as raw text on purpose.** Those rows were dead-lettered
precisely because their values will not parse. Casting `1,250.00` to a decimal
in the warehouse would fail for the same reason it failed in Python. They are
kept readable so a human can look at them and a fixed parser can replay them.

Six dbt tests assert what the Python layer already guarantees: `txn_id` unique
and not null, `amount` not null, `currency` and `status` within their allowed
sets, and every dead letter carrying a reason. Python enforces this today; the
tests catch the day a change quietly stops enforcing it.

---

## Orchestration

```powershell
astro dev start
```

One DAG, four tasks, chained so each runs only if the one before it succeeded:

```
extract_validate_transform  →  dbt_seed  →  dbt_run  →  dbt_test
```

Credentials reach the containers through an untracked `.env`; `profiles.yml`
reads them with `env_var`, so no token is ever committed.

`dbt_test` is the task that earns its keep. A future export that breaks the
rules turns it red, instead of quietly publishing wrong numbers.

---

## Not built yet

| | |
|---|---|
| JSON ingestion | `data/transactions.json` holds the same 51 rows nested differently. Feeding it through the same validator needs a normaliser in front of `Record`. |
| Incremental models | Every run is a full refresh. Fine at 51 rows, wrong at 51 million. |
| A real source | The CSV is baked into the Docker image. In production it would be read from object storage each run. |
