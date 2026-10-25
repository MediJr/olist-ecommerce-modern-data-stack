{#
    Si une même ligne arrive dans deux livraisons (export corrigé, mois relivré), on garde la plus récente.
    Le lac conserve toutes les versions ; c'est la couche staging qui choisit, de façon explicite et testée.
#}
{% macro latest_delivery(key_columns) -%}
    qualify row_number() over (
        partition by {{ key_columns | join(', ') }}
        order by _ingested_at desc, delivery_month desc
    ) = 1
{%- endmacro %}
