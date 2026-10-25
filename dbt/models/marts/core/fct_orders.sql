-- Table de faits au grain de la commande : livraison, satisfaction, paiement.
-- Les montants sont déjà agrégés par commande dans int_orders : aucune jointure ne peut les multiplier ici.
select
    order_id,
    customer_unique_id,
    purchase_date,
    purchase_month,
    customer_state,
    order_status,
    is_valid,
    customer_order_number,
    item_count,
    items_value,
    freight_value,
    payment_value,
    payment_count,
    main_payment_type,
    max_installments,
    review_score,
    review_has_comment,
    delivery_days,
    delay_days,
    is_late
from {{ ref('int_orders') }}
