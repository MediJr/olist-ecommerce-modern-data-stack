-- Une ligne par commande. Dates en heure locale de Brasília : la source ne donne pas de fuseau, on n'en invente pas.
select
    order_id,
    customer_id,
    order_status,
    cast(order_purchase_timestamp as timestamp)      as purchased_at,
    cast(order_approved_at as timestamp)             as approved_at,
    cast(order_delivered_carrier_date as timestamp)  as shipped_at,
    cast(order_delivered_customer_date as timestamp) as delivered_at,
    cast(order_estimated_delivery_date as date)      as estimated_delivery_date,
    delivery_month,
    _ingested_at
from {{ source('bronze', 'orders') }}
{{ latest_delivery(['order_id']) }}
