# ADR 004 : Tableau de bord Streamlit plutôt que Metabase

- **Date :** 2026-10-23
- **Statut :** Acceptée par le client (remplace la décision D4 du cadrage)

## Contexte

Le cadrage prévoyait Metabase. Or **DuckDB n'accepte qu'un seul processus en écriture**, et aucun écrivain tant qu'un autre
processus tient le fichier ouvert. Metabase garde ses connexions ouvertes en permanence : chaque reconstruction dbt échouerait
sur un fichier verrouillé.

## Décision

Un tableau de bord **Streamlit**, écrit en Python et versionné avec le projet (*dashboard as code*) :

- il ne lit **que la couche marts** ;
- chaque requête ouvre l'entrepôt **en lecture seule**, puis le referme aussitôt (mise en cache 5 minutes) ;
- dans Docker, le volume de l'entrepôt est monté **en lecture seule** pour ce service ;
- il est bilingue (français et anglais) et couvert par un test de fumée dans l'intégration continue.

## Alternatives écartées

| Option | Raison du rejet |
|---|---|
| Metabase sur DuckDB | Verrou permanent du fichier : dbt ne peut plus écrire |
| Metabase + PostgreSQL de diffusion | Deux services et une étape de copie de plus ; pertinent si le comité veut créer ses propres questions |
| Graphiques statiques seulement | Le client a demandé un outil interactif, pas seulement un rapport |

## Conséquences

- ✅ Le tableau de bord évolue comme le code : relu, versionné, testé
- ⚠️ Le comité ne peut pas créer ses propres graphiques sans écrire de Python : piste d'évolution notée dans le rapport
