-- Une ligne par commande, avec TOUTES les règles métier du cadrage, écrites une seule fois :
--   D2  commande valide (compte dans le CA) ;  D3  client = customer_unique_id, rang de sa commande ;
--   et les indicateurs de livraison (délai, retard).
-- Chaque table enfant est agrégée AVANT la jointure : joindre articles et paiements ligne à ligne
-- multiplierait les montants (une commande à 2 articles et 2 paiements donnerait 4 lignes).

with items as (
    select
        order_id,
        count(*)            as item_count,
        sum(price)          as items_value,
        sum(freight_value)  as freight_value
    from {{ ref('stg_order_items') }}
    group by order_id
),

payments as (
    select
        order_id,
        sum(payment_value)  as payment_value,
        count(*)            as payment_count,
        max(installments)   as max_installments,
        -- Mode principal = celui qui a réglé le plus gros montant (en cas d'égalité, le premier paiement)
        arg_max(payment_type, payment_value * 1000 - payment_sequential)  as main_payment_type
    from {{ ref('stg_order_payments') }}
    group by order_id
),

reviews as (
    -- Une commande peut avoir plusieurs avis : on garde le plus récent.
    select order_id, review_score, has_comment
    from {{ ref('stg_order_reviews') }}
    qualify row_number() over (partition by order_id order by created_at desc, answered_at desc) = 1
),

orders as (
    select
        o.order_id,
        c.customer_unique_id,
        o.customer_id,
        c.state                                       as customer_state,
        c.city                                        as customer_city,
        c.zip_code_prefix                             as customer_zip_code_prefix,
        o.order_status,
        o.order_status not in (
            {%- for s in var('invalid_order_statuses') %}'{{ s }}'{{ ', ' if not loop.last }}{% endfor -%}
        )                                             as is_valid,
        o.purchased_at,
        cast(o.purchased_at as date)                  as purchase_date,
        date_trunc('month', o.purchased_at)::date     as purchase_month,
        o.approved_at,
        o.shipped_at,
        o.delivered_at,
        o.estimated_delivery_date,
        coalesce(i.item_count, 0)                     as item_count,
        coalesce(i.items_value, 0)                    as items_value,
        coalesce(i.freight_value, 0)                  as freight_value,
        coalesce(p.payment_value, 0)                  as payment_value,
        coalesce(p.payment_count, 0)                  as payment_count,
        p.max_installments,
        p.main_payment_type,
        r.review_score,
        r.has_comment                                 as review_has_comment,
        -- Livraison : seulement si la commande est livrée ET datée (quelques commandes « livrées » n'ont pas de date)
        case when o.order_status = 'delivered' and o.delivered_at is not null
             then date_diff('day', cast(o.purchased_at as date), cast(o.delivered_at as date)) end
                                                      as delivery_days,
        case when o.order_status = 'delivered' and o.delivered_at is not null
             then date_diff('day', o.estimated_delivery_date, cast(o.delivered_at as date)) end
                                                      as delay_days      -- > 0 : en retard ; <= 0 : à l'heure ou en avance
    from {{ ref('stg_orders') }} o
    join {{ ref('stg_customers') }} c using (customer_id)
    left join items i using (order_id)
    left join payments p using (order_id)
    left join reviews r using (order_id)
)

select
    *,
    delay_days > 0  as is_late,
    -- Rang de la commande dans l'historique du client (commandes valides uniquement) : 1 = première commande
    case when is_valid then
        row_number() over (
            partition by customer_unique_id, is_valid order by purchased_at, order_id
        )
    end             as customer_order_number
from orders
