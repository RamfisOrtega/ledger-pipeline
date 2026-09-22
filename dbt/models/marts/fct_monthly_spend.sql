select
    counterparty,
    counterparty_country,
    date_trunc('month', booked_at)         as month,
    count(*)                               as transaction_count,
    round(sum(amount * fx_rate_to_chf), 2) as total_chf
from {{ ref('stg_transactions') }}
where status = 'booked'
group by counterparty, counterparty_country, month
