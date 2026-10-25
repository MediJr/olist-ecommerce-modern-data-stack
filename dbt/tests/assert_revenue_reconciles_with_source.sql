-- Critère de recette C4 : le CA du tableau de bord est ÉGAL au total calculé directement sur la couche bronze.
-- Le calcul de contrôle est volontairement indépendant de dbt (aucun ref) : si une jointure des marts
-- perd ou duplique des articles, les deux totaux divergent et le test échoue.
with source_total as (
    select sum(cast(i.price as decimal(12, 2))) as revenue
    from {{ source('bronze', 'order_items') }} i
    join {{ source('bronze', 'orders') }} o using (order_id)
    where o.order_status not in (
        {%- for s in var('invalid_order_statuses') %}'{{ s }}'{{ ', ' if not loop.last }}{% endfor -%}
    )
),

mart_total as (
    select sum(revenue) as revenue from {{ ref('rpt_revenue_monthly') }}
)

select s.revenue as source_revenue, m.revenue as mart_revenue
from source_total s, mart_total m
where s.revenue is distinct from m.revenue
