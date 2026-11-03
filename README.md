  retirés lors de la transformation

# BOAMP-it-pipeline

Pipeline de données des appels d'offres IT et télécoms publiés au BOAMP depuis 2020.

## Thématique

## Source et licence

- Source : API BOAMP de la DILA (plateforme Opendatasoft), endpoint `records` de l'API Explore v2.1
- Licence : Licence Ouverte / Open Licence (Etalab)
- Mise à jour : publication deux fois par jour, 7 jours sur 7
- Périmètre retenu : annonces publiées depuis le 01/01/2020 portant au moins un des descripteurs

  - Volume au 03/11/2026 : 41 934 annonces
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

## Dataset publié
