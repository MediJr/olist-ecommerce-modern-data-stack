-- Une ligne par couple (avis, commande). Le texte des avis (en portugais) est conservé mais hors périmètre d'analyse.
select
    review_id,
    order_id,
    cast(review_score as integer)               as review_score,
    review_comment_title                        as comment_title,
    review_comment_message                      as comment_message,
    review_comment_message is not null          as has_comment,
    cast(review_creation_date as timestamp)     as created_at,
    cast(review_answer_timestamp as timestamp)  as answered_at,
    delivery_month,
    _ingested_at
from {{ source('bronze', 'order_reviews') }}
{{ latest_delivery(['review_id', 'order_id']) }}
