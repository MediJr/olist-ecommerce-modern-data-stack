# 02 · Compte rendu de la réunion de cadrage

> 🎭 **Scénario fictif** : voir le [brief client](2026-10-23-01-brief-client.md).

| | |
|---|---|
| **Date** | 2026-10-23 |
| **Durée** | 1 h, en visioconférence |
| **Participants** | Claire Dumont (directrice du développement international), Hugo Martin (analyste données), le data engineer |

---

## 1. Décisions prises

| # | Sujet | Décision |
|---|---|---|
| D1 | **Mises à jour** | La marketplace partenaire enverra un **export mensuel** (un dossier de fichiers CSV par mois). Pour la mission, on **simule** ces livraisons en découpant le jeu public par mois d'achat. Le pipeline doit traiter un mois **sans retraiter les autres**. |
| D2 | **Chiffre d'affaires** | CA = **prix des articles** (`price`), hors fret. Le fret est suivi à part (Q5). Seules les commandes **non annulées et non indisponibles** comptent. La définition sera écrite **une seule fois**, dans dbt, et réutilisée partout. |
| D3 | **Client qui revient** | Un client est identifié par `customer_unique_id`, **pas** par `customer_id`, qui change à chaque commande (à vérifier au profilage). Client fidèle = au moins **2 commandes** à des dates différentes. |
| D4 | **Tableau de bord** | **Metabase** (open source, gratuit), qui lit uniquement la couche *marts*. |
| D5 | **Maintenance par Hugo** | Toute modification passe par une *pull request* : **intégration continue** GitHub Actions qui construit et teste le projet dbt sur un échantillon. |
| D6 | **Langue** | Noms de tables et de colonnes en anglais (standard dbt), documentation et rapport en français, rapport également en anglais. |

## 2. Questions business retenues

| # | Question | Pourquoi c'est utile au comité |
|---|---|---|
| **Q1** | Quelles **catégories** et quels **États** font le chiffre d'affaires, et comment évolue-t-il chaque mois ? | Choisir les collections et les régions de lancement |
| **Q2** | Quelle part des clients **revient** acheter, et après combien de temps ? | Décider si l'on investit dans la fidélisation ou dans l'acquisition |
| **Q3** | Le **retard de livraison** dégrade-t-il la **note** laissée par le client ? | Mesurer l'enjeu du choix du transporteur |
| **Q4** | Comment les clients **paient**-ils (carte, *boleto*, nombre de versements), et le panier moyen change-t-il selon le mode ? | Préparer l'offre de paiement |
| **Q5** | Quelle part du prix représente le **fret**, selon l'État de destination ? | Évaluer le coût logistique par région |

## 3. Points d'attention sur les données (à vérifier au profilage)

- `customer_id` vs `customer_unique_id` : risque de **sous-estimer la fidélité** si l'on compte le mauvais identifiant.
- Une commande peut avoir **plusieurs lignes de paiement** (bon d'achat + carte) : risque de **doubler le CA** si l'on joint mal.
- Une commande peut avoir **plusieurs articles** : le grain de la table de faits doit être choisi explicitement.
- Catégories en **portugais**, avec une table de traduction peut-être incomplète.
- Table de géolocalisation volumineuse, avec plusieurs coordonnées par code postal.
- Dates de livraison manquantes pour certaines commandes « livrées ».

## 4. Actions

| Action | Responsable | Échéance |
|---|---|---|
| Télécharger le jeu Olist depuis Kaggle (compte personnel requis) | Client (Hugo) | 2026-10-23 |
| Rédiger le cahier des charges | Data engineer | 2026-10-23 |
| Valider le cahier des charges | Claire Dumont | 2026-10-23 |

➡️ Suite : [03 · Cahier des charges](2026-10-23-03-cahier-des-charges.md)
