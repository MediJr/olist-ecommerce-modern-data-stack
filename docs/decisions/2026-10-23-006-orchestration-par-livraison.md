# ADR 006 : Une livraison = une partition, déclenchée par un capteur

- **Date :** 2026-10-23 (complétée le 2026-10-25)
- **Statut :** Acceptée

## Contexte

Le partenaire dépose un dossier par mois (décision D1). Il faut traiter chaque livraison **dès qu'elle est complète**, pouvoir
**rejouer** un mois corrigé sans doublon, et ne jamais lancer deux écritures DuckDB en même temps.

## Décisions

1. **Marqueur `_SUCCESS`** écrit en dernier par le producteur : un dossier sans marqueur est une livraison en cours, jamais lue.
2. **Partitions dynamiques** (`delivery_month`) : une partition est créée à la réception d'une livraison, plutôt qu'un calendrier fixé
   à l'avance qui afficherait des mois « manquants ».
3. **Capteur** (`landing_sensor`, toutes les 30 s) : une livraison nouvelle **ou relivrée** (date du marqueur modifiée) déclenche le job
   `monthly_delivery` (couche bronze du mois, puis `dbt build`). La clé d'exécution `mois@horodatage` empêche de traiter deux fois la même version.
4. **Écriture idempotente** : une partition bronze est un fichier unique, **remplacé** au rejeu.
5. **Une exécution à la fois** (`tag_concurrency_limits` dans `dagster.yaml`), car DuckDB n'accepte qu'un écrivain.
6. **Amorçage** : dbt joint chaque commande à son produit. Le capteur mensuel attend donc le premier chargement des référentiels.
   Les référentiels qui arrivent avant tout mois sont chargés seuls (`reference_bootstrap`), sans dbt.

## Incident à l'origine de la décision 6

Lors du premier test, référentiels et premier mois ont été déposés ensemble. Le job des référentiels est passé en premier et a lancé dbt
alors qu'aucune commande n'était encore dans le lac : `No files found that match the pattern s3://olist-lake/bronze/order_items/*/*.parquet`.
L'ordre de démarrage d'une plateforme est une dépendance comme une autre : il doit être explicite.

## Conséquences

- ✅ Déposer un dossier suffit : le reste est automatique, tracé, et rejouable
- ✅ Rejouer octobre 2016 a laissé exactement 329 commandes distinctes (critère C3)
- ⚠️ Chaque mois relance un `dbt build` complet (environ 1 min) : un rattrapage de 26 mois prend environ 30 min. Acceptable pour une
  livraison mensuelle ; pour un rattrapage massif, `BackfillPolicy.single_run` permet de tout traiter en une exécution
