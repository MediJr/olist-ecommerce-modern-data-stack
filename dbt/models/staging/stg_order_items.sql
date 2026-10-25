-- Une ligne par article. Montants en réais (BRL), en décimal exact : jamais de float pour de l'argent.
select
    order_id,
    cast(order_item_id as integer)          as order_item_id,
    product_id,
    seller_id,
    cast(shipping_limit_date as timestamp)  as shipping_limit_at,
    cast(price as decimal(12, 2))           as price,
    cast(freight_value as decimal(12, 2))   as freight_value,
    delivery_month,
    _ingested_at
from {{ source('bronze', 'order_items') }}
{{ latest_delivery(['order_id', 'order_item_id']) }}
