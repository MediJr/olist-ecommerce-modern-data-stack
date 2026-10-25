-- Une ligne par point relevé : plusieurs points par préfixe de code postal (agrégés dans la couche intermediate).
select
    geolocation_zip_code_prefix          as zip_code_prefix,
    cast(geolocation_lat as double)      as latitude,
    cast(geolocation_lng as double)      as longitude,
    geolocation_city                     as city,
    upper(geolocation_state)             as state
from {{ source('bronze', 'geolocation') }}
