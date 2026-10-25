-- Une ligne par paiement. Une commande peut en compter plusieurs (jusqu'à 29 dans le jeu).
select
    order_id,
    cast(payment_sequential as integer)    as payment_sequential,
    payment_type,
    cast(payment_installments as integer)  as installments,
    cast(payment_value as decimal(12, 2))  as payment_value,
    delivery_month,
    _ingested_at
from {{ source('bronze', 'order_payments') }}
{{ latest_delivery(['order_id', 'payment_sequential']) }}
