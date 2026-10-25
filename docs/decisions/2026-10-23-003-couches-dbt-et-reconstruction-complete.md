# ADR 003 : Couches bronze, staging, intermediate, marts, et reconstruction complète de l'entrepôt

- **Date :** 2026-10-23
- **Statut :** Acceptée

## Contexte

Les règles métier du cadrage (D2 : commande valide et chiffre d'affaires ; D3 : client réel) doivent être écrites **une seule fois**.
Le profilage a révélé trois pièges qui faussent les chiffres si on les ignore :

| Piège | Effet si on l'ignore |
|---|---|
| `customer_id` change à chaque commande (99 441 valeurs pour 96 096 personnes) | Fidélité presque nulle, faussement |
| 2 961 commandes réglées en plusieurs paiements, 9 803 commandes à plusieurs articles | Une jointure articles × paiements multiplie le CA |
| 98 410 `review_id` pour 99 224 avis | Clé fausse, avis perdus ou dupliqués |

## Décisions

1. **Bronze** (lac) : les livraisons telles que reçues, **tout en texte**, plus deux colonnes de traçabilité (`_source_file`, `_ingested_at`).
2. **Staging** (vues dbt) : un modèle par source ; renommer, typer (`decimal` pour l'argent, jamais `float`), et garder la
   **dernière livraison** d'une même ligne (macro `latest_delivery`). Aucune règle métier.
3. **Intermediate** : `int_orders`, une ligne par commande, où **chaque table enfant est agrégée avant la jointure**. Toutes les règles
   métier sont là, couvertes par trois **tests unitaires dbt**.
4. **Marts** : un schéma en étoile (`fct_order_items` au grain de l'article, `fct_orders`, `dim_customers`, `dim_products`, `dim_sellers`,
   `dim_date`) et une table de reporting par question (`rpt_*`). Le contrat de `fct_order_items` est **imposé** (*enforced*).
5. **Reconstruction complète** à chaque exécution, plutôt que des modèles incrémentaux : 100 000 commandes se reconstruisent en
   une vingtaine de secondes.
6. **Rapprochements avec la source** (tests singuliers) : le CA des marts et le total des paiements doivent être égaux aux totaux
   calculés directement sur la couche bronze, sans passer par dbt.

## Alternatives écartées

| Option | Raison du rejet |
|---|---|
| Modèles dbt incrémentaux | Complexité (fusion, rattrapage) sans gain à ce volume. À reconsidérer au-delà de quelques minutes de construction |
| Typer dès la couche bronze | Une conversion ratée ferait perdre la donnée d'origine ; bronze reste fidèle à la livraison |
| Paquets dbt externes (dbt_utils) | Trois tests génériques maison suffisent, sans dépendance à télécharger |

## Conséquences

- ✅ Une erreur de jointure est détectée par les tests de rapprochement, pas par le comité de direction
- ✅ Hugo modifie une définition à un seul endroit ; les tests et l'intégration continue vérifient le reste
- ⚠️ Les vues staging lisent le lac à chaque requête : elles demandent l'accès S3, contrairement aux marts (tables)
