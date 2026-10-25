-- Une ligne par produit, avec sa catégorie en anglais.
-- Deux catégories n'ont pas de traduction dans la source, et 610 produits n'ont pas de catégorie :
-- on applique une valeur de repli EXPLICITE plutôt que de laisser des cases vides dans le tableau de bord.
select
    p.product_id,
    p.category_name_pt,
    coalesce(
        t.category_name_en,
        case p.category_name_pt
            when 'pc_gamer' then 'pc_gamer'
            when 'portateis_cozinha_e_preparadores_de_alimentos' then 'portable_kitchen_and_food_preparers'
        end,
        case when p.category_name_pt is null then 'unknown' end,
        p.category_name_pt
    )                                   as category,
    t.category_name_en is not null      as has_official_translation,
    p.weight_g,
    p.length_cm,
    p.height_cm,
    p.width_cm,
    p.length_cm * p.height_cm * p.width_cm  as volume_cm3,
    p.photos_qty
from {{ ref('stg_products') }} p
left join {{ ref('stg_category_translation') }} t using (category_name_pt)
