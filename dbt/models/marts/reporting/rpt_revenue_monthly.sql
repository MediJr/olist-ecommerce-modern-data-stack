-- Q1 · Chiffre d'affaires par mois, catégorie et État du client (commandes valides, hors fret).
select
    f.purchase_month,
    p.category,
    f.customer_state,
    sum(f.revenue)               as revenue,
    count(*)                     as items_sold,
    count(distinct f.order_id)   as orders
from {{ ref('fct_order_items') }} f
join {{ ref('dim_products') }} p using (product_id)
where f.is_valid
group by all
