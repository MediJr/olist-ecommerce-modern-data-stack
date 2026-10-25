# ADR 002 : SeaweedFS plutôt que MinIO pour le lac S3 local

- **Date :** 2026-10-23
- **Statut :** Acceptée (remplace le choix de MinIO du cahier des charges, section 7)

## Contexte

Le cahier des charges prévoyait **MinIO**, le stockage S3 local le plus connu. Au moment de l'installation, le téléchargement
de l'image a échoué : `minio/minio` n'existe plus sur Docker Hub, et `quay.io/minio/minio` demande une authentification.
L'éditeur a cessé de distribuer des images Docker publiques de sa version communautaire.

C'est un **risque fournisseur** réel : un composant open source peut changer de modèle de distribution du jour au lendemain.

## Décision

Utiliser **SeaweedFS** (licence Apache 2.0, image publique `chrislusf/seaweedfs`, version figée **4.48**), en mode serveur avec sa
passerelle S3. Le fichier d'identités S3 est généré au démarrage du conteneur à partir de `.env` : aucun secret dans le dépôt.

## Alternatives écartées

| Option | Raison du rejet |
|---|---|
| Compiler MinIO depuis les sources | Effort et maintenance hors de proportion pour un lac local |
| Une ancienne image MinIO trouvée sur un miroir | Source non officielle, sans correctifs de sécurité |
| LocalStack | Émulateur de tout AWS : beaucoup plus lourd pour un seul service |
| Un simple dossier local | Ne prouve pas que le code parle le protocole S3 |

## Conséquences

- ✅ **Aucune ligne de code modifiée** : DuckDB parle S3, peu importe qui est derrière. C'est l'intérêt d'un standard
- ✅ Version d'image figée : la plateforme se reconstruit à l'identique
- ⚠️ SeaweedFS est moins connu que MinIO ; la console web n'est pas utilisée
