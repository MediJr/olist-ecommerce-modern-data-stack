-- Table de faits principale. GRAIN : une ligne par article vendu (order_id, order_item_id).
-- C'est le grain le plus fin qui porte le chiffre d'affaires : on peut toujours agréger vers le haut
-- (commande, catégorie, mois), jamais redescendre.
select
    i.order_id,
    i.order_item_id,
    o.customer_unique_id,
    i.product_id,
    i.seller_id,
    o.purchase_date,
    o.purchase_month,
    o.customer_state,
    o.order_status,
    o.is_valid,
    i.price,
    i.freight_value,
    case when o.is_valid then i.price else 0 end  as revenue     -- définition D2 : prix des articles, commandes valides, hors fret
from {{ ref('stg_order_items') }} i
join {{ ref('int_orders') }} o using (order_id)
