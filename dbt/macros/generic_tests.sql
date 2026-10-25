{#
    Tests génériques maison, pour ne dépendre d'aucun paquet externe.
    Un test dbt est une requête qui renvoie les lignes EN ERREUR : zéro ligne = test réussi.
#}

{% test unique_combination(model, columns) %}
    select {{ columns | join(', ') }}, count(*) as occurrences
    from {{ model }}
    group by {{ columns | join(', ') }}
    having count(*) > 1
{% endtest %}

{% test non_negative(model, column_name) %}
    select * from {{ model }} where {{ column_name }} < 0
{% endtest %}

{% test accepted_brazilian_state(model, column_name) %}
    -- Les 26 États du Brésil et le District fédéral (DF).
    select * from {{ model }}
    where {{ column_name }} not in (
        'AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA',
        'PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO'
    )
{% endtest %}
