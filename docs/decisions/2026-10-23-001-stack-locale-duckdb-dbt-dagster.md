# ADR 001 : Modern data stack locale avec DuckDB, dbt et Dagster

- **Date :** 2026-10-23
- **Statut :** Acceptée

## Contexte

Le client veut deux choses (brief, cadrage) : une étude de marché chiffrée, et un outil que son analyste, Hugo, pourra
**faire évoluer seul, en SQL, sans risque de régression**. Les données arrivent par **livraisons mensuelles**.
Le projet doit tourner sur un poste, sans budget cloud, tout en restant transposable sur le cloud (mission suivante).

## Décisions

| Rôle | Choix | Raison |
|---|---|---|
| Data lake | Stockage objet **compatible S3**, fichiers **Parquet** partitionnés par mois | Même interface qu'Amazon S3 ou Google Cloud Storage : seul l'emplacement change pour passer au cloud |
| Entrepôt | **DuckDB** | Moteur analytique colonnaire en un fichier, qui lit le Parquet sur S3 directement. Rien à administrer |
| Transformations | **dbt** | SQL versionné, testé (tests de données et tests unitaires), documenté, avec le lignage. C'est l'outil standard pour qu'un analyste maintienne les règles métier |
| Orchestration | **Dagster** | Raisonne en *assets* (les données produites) ; intégration native de dbt, où chaque modèle devient un asset et chaque test un contrôle ; partitions et capteurs |

Le lac est désigné par une seule variable, `LAKE_URI` : `s3://olist-lake` en local, un simple dossier dans l'intégration continue.

## Alternatives écartées

| Option | Raison du rejet |
|---|---|
| PostgreSQL comme entrepôt | Moteur orienté transactions, ne lit pas le Parquet ; déjà pratiqué aux projets 1 et 2 |
| Airflow | Raisonne en tâches et non en données ; plus lourd à installer en local ; intégration dbt moins riche |
| Transformations en Python (pandas) | Les règles métier seraient illisibles pour l'analyste du client et testées à part |

## Conséquences

- ✅ La logique métier vit dans dbt, testée à chaque construction ; Dagster montre le graphe complet, du CSV au tableau de bord
- ✅ Le passage au cloud (projet 6 : BigQuery, GCS) ne change ni l'ingestion ni la structure dbt
- ⚠️ DuckDB n'accepte **qu'un seul processus en écriture** : voir les ADR 004 et 006
