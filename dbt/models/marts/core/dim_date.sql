-- Dimension calendrier : une ligne par jour, de la première à la dernière commande (mois complets).
-- Elle permet de filtrer par mois, trimestre ou jour de semaine sans recalculer les dates partout.
with bounds as (
    select
        date_trunc('month', min(purchase_date))                                      as first_day,
        date_trunc('month', max(purchase_date)) + interval 1 month - interval 1 day  as last_day
    from {{ ref('int_orders') }}
)

select
    cast(d.day as date)                       as date_day,
    year(d.day)                               as year,
    quarter(d.day)                            as quarter,
    month(d.day)                              as month,
    cast(date_trunc('month', d.day) as date)  as month_start,
    strftime(d.day, '%Y-%m')                  as year_month,
    isodow(d.day)                             as iso_day_of_week,     -- 1 = lundi … 7 = dimanche
    isodow(d.day) >= 6                        as is_weekend
from bounds, generate_series(bounds.first_day, bounds.last_day, interval 1 day) as d(day)
