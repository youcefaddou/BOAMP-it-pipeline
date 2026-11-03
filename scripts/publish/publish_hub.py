import logging
import os
from pathlib import Path

from datasets import load_dataset
from dotenv import load_dotenv
from huggingface_hub import DatasetCard, DatasetCardData, HfApi

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"
REPO_ID = "golgoxiii/boamp-it-annonces"
VERSION = "v1.0.0"

TEXTE_CARD = """
# Appels d'offres IT et télécoms du BOAMP (2015-2026)

Annonces de marchés publics français portant sur l'informatique et les télécoms,
publiées au BOAMP (Bulletin officiel des annonces des marchés publics) depuis mars 2015.

## Source et licence

- Source : API BOAMP de la DILA (data.gouv.fr)
- Licence de la source : Licence Ouverte / Open Licence (Etalab)
- Réutilisation : merci de citer la source (BOAMP, DILA) et la date de mise à jour

## Périmètre

Annonces portant au moins un des descripteurs : Informatique (prestations de services),
Logiciel, Informatique (matériel), Informatique (maintenance serveurs et réseaux),
Télécommunications.

## Contenu

- `annonces` : une ligne par annonce (identifiant, objet, acheteur, département,
  dates, nature de l'avis, type de marché, titulaire, lien vers l'avis)
- `descripteurs` : une ligne par couple annonce / descripteur

Les contacts (téléphones, e-mails) présents dans la source ont été retirés.

## Limites

- L'année 2015 est incomplète : les données commencent en mars
- Un même acheteur peut apparaître sous plusieurs noms
- Le titulaire n'est renseigné que pour une partie des résultats de marché

## Pipeline

Collecte asynchrone, transformation et chargement : https://github.com/youcefaddou/BOAMP-it-pipeline
"""

def construire_card():
    card_data = DatasetCardData(
        language="fr",
        license="other",
        license_name="licence-ouverte-etalab",
        license_link="https://www.etalab.gouv.fr/licence-ouverte-open-licence",
        pretty_name="Appels d'offres IT et télécoms du BOAMP",
        size_categories=["10K<n<100K"],
        tags=["marchés publics", "boamp", "france"],
    )
    return DatasetCard(f"---\n{card_data.to_yaml()}\n---\n{TEXTE_CARD}")


def main():
    load_dotenv()
    token = os.environ["HF_TOKEN"]
    api = HfApi(token=token)

    api.create_repo(REPO_ID, repo_type="dataset", private=True, exist_ok=True)
    construire_card().push_to_hub(REPO_ID, token=token)
    logging.info("Dataset Card publiée")

    for nom in ["annonces", "descripteurs"]:
        ds = load_dataset("parquet", data_files=str(PROCESSED_DIR / f"{nom}_*.parquet"), split="train")
        ds.push_to_hub(REPO_ID, config_name=nom, private=True, token=token)
        logging.info(f"{nom} : {ds.num_rows} lignes publiées")

    api.create_tag(REPO_ID, tag=VERSION, repo_type="dataset", exist_ok=True)
    logging.info(f"Tag {VERSION} créé")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()