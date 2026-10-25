# Changelog

Toutes les évolutions notables du projet sont consignées ici.
Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Le projet suit le [versionnage sémantique](https://semver.org/lang/fr/).

## [1.0.0] - 2026-10-25

Première version livrée au client.

### Ajouté
- Dossier de mission : brief client, compte rendu de cadrage, cahier des charges (CAJ-2026-001)
- Plateforme Docker Compose : lac S3 (SeaweedFS), Dagster, tableau de bord Streamlit ; image unique en Python 3.13
- Livraisons mensuelles simulées (marqueur `_SUCCESS`) et ingestion contrôlée vers la couche bronze (Parquet partitionné par mois)
- Projet dbt : 9 modèles staging, 2 intermediate, 6 du schéma en étoile, 5 de reporting ; 69 tests de données,
  3 tests unitaires, 3 rapprochements avec la source, 1 contrat imposé
- Dagster : partitions dynamiques, capteurs (livraisons et référentiels), amorçage, une exécution à la fois, délai maximal
- Tableau de bord bilingue (5 questions, 10 graphiques), 14 tests pytest, intégration continue GitHub Actions
- 7 graphiques en français et en anglais, rapports LaTeX, dictionnaire de données, 6 ADR, journal de bord, PV de recette

### Modifié (par rapport au cahier des charges)
- MinIO remplacé par SeaweedFS (image MinIO plus distribuée publiquement)
- Metabase remplacé par Streamlit (un seul écrivain DuckDB)
- Exécution locale remplacée par une plateforme entièrement dans Docker (Smart App Control sous Windows)

### Corrigé (pendant le développement)
- dbt lancé avant l'arrivée de la première commande : règles d'amorçage des capteurs
- Exécution figée 83 min (sous-processus bloqués au chargement de DLL) : exécution dans un seul processus, délai maximal de 15 min
- Période par défaut du tableau de bord écrite en dur : calculée à partir des données
- `GROUP BY ALL` refusé sur une expression mêlant agrégat et colonne : regroupement explicite
