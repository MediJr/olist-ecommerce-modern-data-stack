-- Q3 · Note client selon le retard de livraison (commandes livrées, datées et notées).
with orders as (
    select
        *,
        case
            when delay_days <= -15 then 1
            when delay_days <= -8  then 2
            when delay_days <= 0   then 3
            when delay_days <= 3   then 4
            when delay_days <= 7   then 5
            when delay_days <= 14  then 6
            else 7
        end as bucket_order
    from {{ ref('fct_orders') }}
    where delay_days is not null and review_score is not null
)

select
    bucket_order,
    case bucket_order
        when 1 then 'early_15d_plus'
        when 2 then 'early_8_14d'
        when 3 then 'early_1_7d_or_on_time'
        when 4 then 'late_1_3d'
        when 5 then 'late_4_7d'
        when 6 then 'late_8_14d'
        else 'late_15d_plus'
    end                                                     as delay_bucket,
    count(*)                                                as orders,
    round(avg(review_score), 2)                             as avg_review_score,
    round(avg(case when review_score <= 2 then 1 else 0 end), 4)  as low_score_share
from orders
group by bucket_order
order by bucket_order
