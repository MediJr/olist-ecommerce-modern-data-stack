-- Q4 · Mode de paiement principal et nombre de versements (commandes valides).
select
    main_payment_type,
    case
        when max_installments <= 1  then '1x'
        when max_installments <= 3  then '2-3x'
        when max_installments <= 6  then '4-6x'
        when max_installments <= 10 then '7-10x'
        else '11x+'
    end                                  as installments_bucket,
    count(*)                             as orders,
    round(avg(payment_value), 2)         as avg_order_value,
    sum(payment_value)                   as total_paid
from {{ ref('fct_orders') }}
where is_valid and main_payment_type is not null
group by all
