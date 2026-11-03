  retirés lors de la transformation

# BOAMP-it-pipeline

Pipeline de données des appels d'offres IT et télécoms publiés au BOAMP depuis 2020.

## Thématique

## Source et licence

- Source : API BOAMP de la DILA (plateforme Opendatasoft), endpoint `records` de l'API Explore v2.1
- Licence : Licence Ouverte / Open Licence (Etalab)
- Mise à jour : publication deux fois par jour, 7 jours sur 7
- - Périmètre retenu : annonces publiées depuis le début des données (2 mars 2015) portant au moins un des descripteurs ...
- - Volume au 03/11/2026 : 84 809 annonces (2015 incomplète, les données commencent en mars
- - Contraintes de l'API : 100 résultats max par page, offset + limit <= 10 000,
- d'où une collecte découpée par fenêtres mensuelles
- - Formats du champ `donnees` : schéma BOAMP classique de 2020 à janvier 2024,
- eForms européen depuis janvier 2024 (voir le champ `source_schema`)
- - Titulaire : champ plat `titulaire`, rempli pour environ 75 % des résultats de marché
- - Montants : uniquement dans `donnees`, structure différente selon le format
- - Données personnelles : `donnees` contient des téléphones et e-mails de contact,
- retirés lors de la transformation

## Structure du dépôt

## Installation



```bash
podman run -d --name boamp-postgres -e POSTGRES_USER=boamp -e POSTGRES_PASSWORD=boamp \
  -e POSTGRES_DB=boamp -p 5432:5432 -v boamp-pgdata:/var/lib/postgresql \
  docker.io/library/postgres:18
podman exec -i boamp-postgres psql -U boamp -d boamp < sql/schema.sql
```

## Relancer le pipeline de zéro

## Choix techniques

### Ingestion (scripts/ingest/ingest_boamp.py)

- Collecte asynchrone avec aiohttp : une seule session, 5 requêtes simultanées
  max (Semaphore + TCPConnector), timeout de 30 s par requête
- Découpage par mois (141 mois depuis mars 2015) puis par pages de 100,
  pour rester sous la limite offset + limit <= 10 000 de l'API
- Tri par idweb pour une pagination stable
- Sortie en JSON Lines dans data/raw/, un fichier par page :
  boamp_AAAA-MM_pNNN.jsonl
- Robustesse : jusqu'à 5 tentatives avec backoff exponentiel + jitter sur les erreurs
  temporaires (429, 500, 502, 503, 504, timeouts), pas de retry sur les erreurs 4xx
- Reprise : data/raw/checkpoint.json liste les mois déjà collectés, ils sont sautés
  à la relance (le mois en cours est toujours recollecté)
- Logs : terminal + logs/ingest.log

Mesures du 03/11/2026 : 84 809 annonces, 922 fichiers, 739 Mo, 135 s.

### Transformation (scripts/transform/transform_boamp.py)

- Outil : Pandas, car les données utiles tiennent en mémoire une fois le champ
  `donnees` retiré (premier choix conseillé par le cours avant HF Datasets ou Spark)
- Traitement par lots : une année à la fois, jamais les 84 809 annonces en même temps
- Validation : idweb, date de parution et objet obligatoires, sinon quarantaine dans
  data/raw/quarantine/invalid_AAAA.jsonl (donnée brute + raison + horodatage)
- Nettoyage : champs plats conservés, `donnees` et `gestion` retirés (ils contiennent
  les contacts), dates typées, espaces superflus supprimés
- Dédoublonnage sur idweb en gardant la dernière version
- Sorties : annonces_AAAA.parquet et descripteurs_AAAA.parquet (une ligne par
  couple annonce / descripteur)

Mesures du 03/11/2026 : 84 809 annonces, 0 en quarantaine, 4,3 s, 7,7 Mo de Parquet
(contre 739 Mo de JSON Lines brut).

### Base SQL (sql/schema.sql, scripts/load/load_boamp.py)

- PostgreSQL 18 lancé avec Podman (voir Installation)
- Tables : annonces (clé primaire idweb, NOT NULL, CHECK sur type_marche) et
  annonce_descripteurs (clé primaire composée, clé étrangère vers annonces)
- Chargement : to_sql vers des tables de staging, puis INSERT ... SELECT avec
  ON CONFLICT, le tout dans une seule transaction : relançable sans doublons
- Réconciliation source / cible par FULL JOIN (sql/reconciliation.sql) : 0 écart

Mesures du 03/11/2026 : 84 809 annonces, 144 229 descripteurs, 22 s.

## Dataset publié
