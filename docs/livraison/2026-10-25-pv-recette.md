# Procès-verbal de recette

> 🎭 **Scénario fictif** : voir le [brief client](../mission/2026-10-23-01-brief-client.md).

| | |
|---|---|
| **Référence** | CAJ-2026-001 |
| **Version livrée** | 1.0.0 |
| **Date** | 2026-10-25 |
| **Environnement** | Poste neuf simulé : volumes Docker supprimés, zone de dépôt vide, image reconstruite |
| **Participants** | Claire Dumont, Hugo Martin (Maison Caju), le data engineer |

## Déroulé

1. `docker compose up -d --build` : lac S3, Dagster et tableau de bord démarrés en **8 s** (image déjà construite ; première construction : 8 min 40).
2. Dépôt des référentiels et des 26 livraisons mensuelles dans `data/landing/`.
3. Traitement **entièrement automatique** par les capteurs Dagster : 1 chargement des référentiels et 26 exécutions mensuelles,
   **27 réussites sur 27**, en **18 min** (19 s de traitement médian par mois).

## Critères d'acceptation

| # | Critère | Résultat | Preuve |
|---|---|---|---|
| C1 | Le projet se lance sur un poste neuf en suivant le README | ✅ | 27/27 exécutions réussies depuis des volumes vides |
| C2 | Chaque mois est une partition ; traiter un mois ne retraite pas les autres | ✅ | Partitions dynamiques `delivery_month`, une exécution par livraison |
| C3 | Rejouer un mois ne crée aucun doublon | ✅ | Octobre 2016 relivré : 329 commandes distinctes avant et après le rejeu ; test `test_replaying_a_month_replaces_it_instead_of_duplicating` |
| C4 | Le CA des marts est égal au total des articles valides de la source | ✅ | Test `assert_revenue_reconciles_with_source` : 13 494 400,74 BRL des deux côtés |
| C5 | Tous les tests dbt passent ; chaque modèle est documenté | ✅ | `dbt build` : 94/94 (22 modèles, 69 tests de données, 3 tests unitaires) |
| C6 | L'intégration continue échoue si un test casse | ✅ | Fret ajouté au CA : refus du **contrat** ; avec le même type, échec du **rapprochement** (code de sortie 1) |
| C7 | Le tableau de bord répond aux questions Q1 à Q5 | ✅ | 5 onglets, 10 graphiques, FR/EN, test de fumée dans la CI |
| C8 | Aucun secret ni donnée brute n'est versionné | ✅ | `.env`, `data/` et l'historique Dagster exclus ; seul un échantillon de 450 commandes (CC BY-NC-SA) est versionné |

## Écarts par rapport au cahier des charges

| Prévu | Livré | Raison | ADR |
|---|---|---|---|
| MinIO | SeaweedFS | L'image MinIO n'est plus distribuée publiquement | 002 |
| Metabase | Streamlit | DuckDB n'accepte qu'un écrivain : Metabase bloquerait dbt | 004 |
| Exécution locale sous Windows | Plateforme dans Docker | Smart App Control bloque des bibliothèques Python non signées | 005 |

## Réserves

- Données de 2016 à 2018 : les conclusions décrivent la structure du marché, pas son état actuel.
- `dagster dev` regroupe serveur et démon dans un conteneur, avec un historique en SQLite : adapté à un poste, pas à un serveur de production.

## Décision

**Recette prononcée sans réserve bloquante.**

| | Client | Prestataire |
|---|---|---|
| **Nom** | Claire Dumont | Data engineer |
| **Date** | 2026-10-25 | 2026-10-25 |
| **Mention** | Bon pour réception | Livré |
