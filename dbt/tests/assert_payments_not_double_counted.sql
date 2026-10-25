-- Les paiements agrégés par commande doivent redonner exactement le total des paiements livrés.
-- Un écart signifierait qu'une jointure a multiplié (ou perdu) des lignes de paiement.
with source_total as (
    select sum(cast(payment_value as decimal(14, 2))) as paid from {{ source('bronze', 'order_payments') }}
),

fact_total as (
    select sum(payment_value) as paid from {{ ref('fct_orders') }}
)

select s.paid as source_paid, f.paid as fact_paid
from source_total s, fact_total f
where s.paid is distinct from f.paid
