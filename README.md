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

Mesures du 03/11/2026 : 84 809 annonces, 922 fichiers, 739 Mo, 135 s.

## Dataset publié
