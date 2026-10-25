-- Une ligne par client RÉEL (customer_unique_id), avec son historique d'achat et sa localisation.
-- Compter les clients sur customer_id (une valeur par commande) ferait croire que personne ne revient jamais.
with orders as (
    select * from {{ ref('int_orders') }}
),

latest_address as (
    -- Adresse de la commande la plus récente : un client peut déménager.
    select customer_unique_id, customer_state, customer_city, customer_zip_code_prefix
    from orders
    qualify row_number() over (partition by customer_unique_id order by purchased_at desc, order_id desc) = 1
),

history as (
    select
        customer_unique_id,
        count(*)                                                    as orders_total,
        count(*) filter (where is_valid)                            as valid_orders,
        min(purchased_at) filter (where is_valid)                   as first_order_at,
        max(purchased_at) filter (where is_valid)                   as last_order_at,
        min(purchased_at) filter (where customer_order_number = 2)  as second_order_at,
        coalesce(sum(items_value) filter (where is_valid), 0)       as lifetime_revenue
    from orders
    group by customer_unique_id
)

select
    h.customer_unique_id,
    a.customer_state,
    a.customer_city,
    a.customer_zip_code_prefix,
    z.latitude,
    z.longitude,
    h.orders_total,
    h.valid_orders,
    h.first_order_at,
    h.last_order_at,
    cast(date_trunc('month', h.first_order_at) as date)        as cohort_month,
    h.second_order_at,
    date_diff('day', h.first_order_at, h.second_order_at)      as days_to_second_order,
    h.valid_orders >= 2                                        as is_repeat_customer,
    h.lifetime_revenue
from history h
join latest_address a using (customer_unique_id)
left join {{ ref('int_zip_code_locations') }} z on z.zip_code_prefix = a.customer_zip_code_prefix
