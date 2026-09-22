select
    txn_id,
    cast(booked_at as date) as booked_at,
    account,
    counterparty,
    counterparty_country,
    category,
    cast(amount as decimal(18, 2)) as amount,
    upper(currency) as currency,
    cast(fx_rate_to_chf as double) as fx_rate_to_chf,
    status
from {{ ref('transactions') }}
