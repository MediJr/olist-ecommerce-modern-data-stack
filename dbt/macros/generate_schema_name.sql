{#
    Par défaut, dbt préfixe les schémas personnalisés par le schéma de la cible (main_staging, main_marts…).
    On garde des noms courts et stables : staging, intermediate, marts. Le tableau de bord lit toujours « marts ».
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name | trim if custom_schema_name is not none else target.schema }}
{%- endmacro %}
