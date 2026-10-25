select
    s.seller_id,
    s.state  as seller_state,
    s.city   as seller_city,
    s.zip_code_prefix,
    z.latitude,
    z.longitude
from {{ ref('stg_sellers') }} s
left join {{ ref('int_zip_code_locations') }} z using (zip_code_prefix)
