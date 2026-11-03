  retirés lors de la transformation

# BOAMP-it-pipeline

Pipeline de données des appels d'offres IT et télécoms publiés au BOAMP depuis 2020.

## Thématique

Les marchés publics informatiques et télécoms en France : qui achète, quoi,
combien de temps les entreprises ont pour répondre, et qui remporte les marchés.
Les données viennent du BOAMP, où l'État et les collectivités publient leurs
appels d'offres et leurs résultats.

## Structure du dépôt

    sql/                 schéma, chargement, analyses, index, réconciliation
    scripts/ingest/      collecte asynchrone depuis l'API BOAMP
    scripts/transform/   nettoyage et passage en Parquet
    scripts/load/        chargement dans PostgreSQL
    scripts/publish/     publication sur le Hugging Face Hub
    data/raw/            JSON Lines bruts (non versionnés)
    data/processed/      Parquet transformés (non versionnés)
    tests/               tests pytest

## Installation

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env   # puis renseigner DATABASE_URL et HF_TOKEN

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

```bash
python scripts/ingest/ingest_boamp.py
python scripts/transform/transform_boamp.py
podman exec -i boamp-postgres psql -U boamp -d boamp < sql/schema.sql
python scripts/load/load_boamp.py
podman exec -i boamp-postgres psql -U boamp -d boamp < sql/index.sql
python scripts/publish/publish_hub.py
```

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

## Analyses (sql/)

| Fichier                         | Question                                           | Notions SQL                        |
| ------------------------------- | -------------------------------------------------- | ---------------------------------- |
| 01_volume_annuel.sql            | Annonces IT par an et par nature                   | GROUP BY                           |
| 02_top_acheteurs.sql            | Top 5 des acheteurs par an                         | CTE, ROW_NUMBER, top N             |
| 03_evolution_mensuelle.sql      | Volume mensuel, moyenne mobile 12 mois, variation  | generate_series, ROWS BETWEEN, LAG |
| 04_repartition_descripteurs.sql | Catégories les plus fréquentes et leur part      | Jointure, SUM() OVER ()            |
| 05_top_titulaires.sql           | Entreprises qui gagnent le plus de marchés IT     | CTE, DISTINCT anti fan-out, RANK   |
| 06_delai_reponse.sql            | Délai moyen pour répondre par famille de marché | Calcul de dates, GROUP BY          |
| 07_acheteurs_perdus.sql         | Acheteurs actifs en 2024 sans avis en 2025         | NOT EXISTS (anti-join)             |

Limite : un même acheteur peut apparaître sous plusieurs noms
(ex. " Voies navigables de France " et " VNF Siège Béthune ")

### Index justifié par EXPLAIN ANALYZE (sql/index.sql, sql/explain_07.sql)

Requête 07 (anti-join NOT EXISTS) : le plan montrait deux Parallel Seq Scan qui
lisaient toute la table pour ne garder qu'environ 4 % des lignes (filtre sur
nature_libelle et dateparution).

Index composite `(nature_libelle, dateparution)` : colonne d'égalité en premier,
colonne de plage ensuite.

|                | Avant                | Après               |
| -------------- | -------------------- | -------------------- |
| Accès         | Parallel Seq Scan x2 | Bitmap Index Scan x2 |
| Buffers        | 14 458               | 543                  |
| Execution Time | 29,7 ms              | 15,2 ms              |

## Dataset publié

- Hub : golgoxiii/boamp-it-annonces (privé pendant le développement)
- Version : v1.0.0
- Deux configurations : `annonces` (84 809 lignes) et `descripteurs` (144 229 lignes)
- Licence : Licence Ouverte / Open Licence (Etalab), celle de la source
- Script : scripts/publish/publish_hub.py (Dataset Card, push_to_hub, tag)

Chargement :

    from datasets import load_dataset
    ds = load_dataset("golgoxiii/boamp-it-annonces", "annonces", revision="v1.0.0")
