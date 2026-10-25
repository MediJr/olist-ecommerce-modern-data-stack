-- Q2 · Rétention par cohorte. Une cohorte = les clients dont la PREMIÈRE commande valide tombe le même mois.
-- Pour chaque cohorte : combien de ses clients repassent commande 1, 2, 3… mois plus tard.
with activity as (
    select distinct
        c.customer_unique_id,
        c.cohort_month,
        date_diff('month', c.cohort_month, o.purchase_month)  as months_since_first
    from {{ ref('fct_orders') }} o
    join {{ ref('dim_customers') }} c using (customer_unique_id)
    where o.is_valid
),

cohort_size as (
    select cohort_month, count(*) as customers
    from {{ ref('dim_customers') }}
    where cohort_month is not null
    group by cohort_month
)

select
    a.cohort_month,
    a.months_since_first,
    s.customers                                     as cohort_customers,
    count(*)                                        as active_customers,
    round(count(*) / s.customers, 4)                as retention_rate
from activity a
join cohort_size s using (cohort_month)
group by a.cohort_month, a.months_since_first, s.customers
