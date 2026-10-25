# ADR 005 : Toute la plateforme dans Docker

- **Date :** 2026-10-25
- **Statut :** Acceptée

## Contexte

Le pipeline tournait d'abord dans un environnement Python local sous Windows. Deux incidents se sont enchaînés :

1. `dagster-dbt` exige Python **< 3.14**. Python 3.13 a été installé à côté de la 3.14, sans modifier la version par défaut.
2. **Smart App Control**, la protection de Windows 11, a commencé à refuser des bibliothèques compilées non signées : d'abord pandas 3.1,
   puis `grpcio`, dont Dagster a besoin. Pendant une livraison, cinq processus d'ingestion sont restés **figés une heure** au
   chargement de leurs DLL, ce qui a bloqué toute la file d'exécution.

Désactiver Smart App Control est **irréversible** sans réinstaller Windows, et c'est une décision de sécurité qui revient au propriétaire
du poste. Il a choisi de garder la protection.

## Décision

Une **image Docker unique** (`python:3.13-slim`, versions figées dans `requirements.txt`, utilisateur sans privilèges), utilisée par
trois services de `docker-compose.yml` :

| Service | Rôle | Volumes |
|---|---|---|
| `lake` | Stockage S3 (SeaweedFS) | `lake-data` |
| `dagster` | Orchestration, ingestion, dbt | archive (lecture seule), zone de dépôt, `warehouse`, `dagster-home` |
| `dashboard` | Streamlit | `warehouse` en **lecture seule** |

Les outils ponctuels (simulation des livraisons, tests) passent par `docker compose run --rm dagster …`.

## Conséquences

- ✅ Toute la plateforme démarre sur un poste neuf avec `docker compose up -d --build` (critère de recette C1)
- ✅ Windows reste protégé ; le code tourne sous Linux, comme en production
- ✅ Les jobs Dagster s'exécutent dans un seul processus (`in_process_executor`) et ont un délai maximal de 15 min
  (`dagster/max_runtime`) : un blocage ne peut plus retenir la file pendant une heure
- ⚠️ `dagster dev` regroupe le serveur web et le démon dans un conteneur, avec un historique en SQLite. En production, on les séparerait
  avec une base PostgreSQL pour l'historique
- ⚠️ La boucle de développement est plus lente : une modification du code demande de reconstruire l'image
