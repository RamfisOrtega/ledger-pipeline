select
    txn_id,
    booked_at,
    account,
    counterparty,
    counterparty_country,
    category,
    amount,
    currency,
    fx_rate_to_chf,
    status,
    reason
from {{ ref('dead_letters') }}
