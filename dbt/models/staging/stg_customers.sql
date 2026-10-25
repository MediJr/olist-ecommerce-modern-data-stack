-- Un customer_id par commande. Le préfixe de code postal reste du TEXTE : « 01037 » perdrait son zéro en nombre.
select
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix  as zip_code_prefix,
    customer_city             as city,
    upper(customer_state)     as state,
    delivery_month,
    _ingested_at
from {{ source('bronze', 'customers') }}
{{ latest_delivery(['customer_id']) }}
