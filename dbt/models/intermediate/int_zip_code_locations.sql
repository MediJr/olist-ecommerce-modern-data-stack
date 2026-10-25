-- Une position par préfixe de code postal : la MÉDIANE des points relevés, après avoir écarté les points
-- hors du Brésil (erreurs de saisie de la source). La médiane résiste mieux qu'une moyenne à un point aberrant.
select
    zip_code_prefix,
    median(latitude)   as latitude,
    median(longitude)  as longitude,
    count(*)           as points
from {{ ref('stg_geolocation') }}
where latitude between -34 and 6          -- de l'extrême sud (Chuí) à l'extrême nord (Roraima)
  and longitude between -74 and -34       -- de l'Acre à la pointe est (Paraíba)
group by zip_code_prefix
