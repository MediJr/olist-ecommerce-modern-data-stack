-- Q5 · Poids du fret et qualité de livraison selon l'État de destination (commandes valides).
select
    customer_state,
    count(*)                                                    as orders,
    sum(items_value)                                            as revenue,
    sum(freight_value)                                          as freight,
    round(sum(freight_value) / nullif(sum(items_value), 0), 4)  as freight_to_price_ratio,
    round(avg(delivery_days), 1)                                as avg_delivery_days,
    round(avg(case when is_late then 1 else 0 end) filter (where is_late is not null), 4)  as late_share,
    round(avg(review_score), 2)                                 as avg_review_score
from {{ ref('fct_orders') }}
where is_valid
group by customer_state
