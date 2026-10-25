# 01 · Brief client : demande initiale

> 🎭 **Scénario fictif.** L'entreprise *Maison Caju* et ses interlocuteurs sont inventés pour les besoins du portfolio.
> Les données analysées sont réelles : c'est le jeu public **Brazilian E-Commerce Public Dataset by Olist**, publié sur Kaggle
> (environ 100 000 commandes anonymisées, 2016-2018). Ce projet n'est ni commandé, ni validé, ni affilié à Olist.

| | |
|---|---|
| **Date de réception** | 2026-10-23 |
| **Canal** | Email |
| **Client** | Maison Caju, marque française de linge de maison et de décoration (35 salariés, vente en ligne en France et en Belgique) |
| **Interlocutrice** | Claire Dumont, directrice du développement international |
| **Objet** | « Faut-il se lancer sur les marketplaces brésiliennes ? » |

---

## Message reçu

> Bonjour,
>
> Nous étudions le lancement de nos collections au **Brésil**, en passant par les marketplaces locales plutôt que par notre propre site.
> Avant d'engager un budget logistique, notre comité de direction veut des réponses chiffrées :
> - quels **produits** et quelles **régions** font le chiffre d'affaires du e-commerce brésilien ;
> - est-ce que les clients **reviennent** acheter, ou est-ce un marché de « one shot » ;
> - à quel point la **livraison** pèse sur la satisfaction et sur le prix payé ;
> - comment les Brésiliens **paient** (on nous parle du *boleto* et du paiement en plusieurs fois).
>
> Nous avons trouvé un jeu de données public très détaillé, publié par une marketplace brésilienne, mais nous ne savons pas l'exploiter.
>
> Point important : notre analyste, Hugo, connaît bien le SQL. Nous voulons qu'il puisse **faire évoluer les indicateurs lui-même**
> après votre départ, sans casser ce qui marche. Et nous voulons un **tableau de bord** pour le comité, pas seulement un rapport.
>
> Merci d'avance,
> Claire Dumont, Maison Caju

---

## 🔍 Première analyse (interne, avant la réunion de cadrage)

**Ce que le client exprime :** une étude de marché chiffrée, puis un outil qu'il pourra maintenir seul.

**Ce que cela implique techniquement :**
1. **« Hugo doit faire évoluer les indicateurs lui-même, sans casser ce qui marche »** : la logique métier doit vivre dans du **SQL
   versionné, documenté et testé**. C'est exactement le rôle de **dbt**. Chaque modification doit être vérifiée automatiquement
   avant d'être acceptée (**intégration continue**).
2. **« Un jeu de données très détaillé »** : 9 tables liées (commandes, articles, paiements, avis, clients, vendeurs, produits,
   géolocalisation, traduction des catégories). Il faut un vrai **modèle dimensionnel** (schéma en étoile) pour que le tableau de bord
   reste simple et juste.
3. **« Un tableau de bord pour le comité »** : il doit lire des tables **déjà calculées et testées**, jamais les fichiers bruts.
4. **Plusieurs étapes à enchaîner** (ingestion, transformation, tests, rafraîchissement du tableau de bord) : un **orchestrateur**
   doit les lancer dans le bon ordre et signaler les échecs. C'est la limite de cron identifiée au projet précédent.

**Points à clarifier en cadrage :**
- Le jeu est figé (2016-2018). Le client recevra-t-il des mises à jour ? Si oui, sous quelle forme ?
- Qu'appelle-t-on « chiffre d'affaires » : prix des articles, avec ou sans fret, commandes annulées comprises ou non ?
- Qu'appelle-t-on un « client qui revient » ?
- Quel outil de tableau de bord, sachant que le client n'a pas de budget logiciel ?

➡️ Suite : [02 · Compte rendu de la réunion de cadrage](2026-10-23-02-compte-rendu-cadrage.md)
