import logging
import os
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = ROOT / "data" / "processed"

INSERT_ANNONCES = """
INSERT INTO annonces (
    idweb, objet, nomacheteur, code_departement, dateparution, datelimitereponse,
    nature_libelle, famille_libelle, type_marche, procedure_libelle, titulaire,
    annonce_lie, source_schema, url_avis
)
SELECT
    idweb, objet, nomacheteur, code_departement, dateparution::date, datelimitereponse,
    nature_libelle, famille_libelle, type_marche, procedure_libelle, titulaire,
    annonce_lie, source_schema, url_avis
FROM staging_annonces
ON CONFLICT (idweb) DO UPDATE SET
    objet = EXCLUDED.objet,
    nomacheteur = EXCLUDED.nomacheteur,
    code_departement = EXCLUDED.code_departement,
    dateparution = EXCLUDED.dateparution,
    datelimitereponse = EXCLUDED.datelimitereponse,
    nature_libelle = EXCLUDED.nature_libelle,
    famille_libelle = EXCLUDED.famille_libelle,
    type_marche = EXCLUDED.type_marche,
    procedure_libelle = EXCLUDED.procedure_libelle,
    titulaire = EXCLUDED.titulaire,
    annonce_lie = EXCLUDED.annonce_lie,
    source_schema = EXCLUDED.source_schema,
    url_avis = EXCLUDED.url_avis;
"""

INSERT_DESCRIPTEURS = """
INSERT INTO annonce_descripteurs (idweb, descripteur)
SELECT DISTINCT idweb, descripteur
FROM staging_descripteurs
ON CONFLICT (idweb, descripteur) DO NOTHING;
"""


def charger_staging(conn, prefixe, table):
    """Charge les fichiers Parquet d'un type dans une table de staging, année par année."""
    lignes = 0
    fichiers = sorted(PROCESSED_DIR.glob(f"{prefixe}_*.parquet"))
    for i, chemin in enumerate(fichiers):
        df = pd.read_parquet(chemin)
        df.to_sql(
            table,
            conn,
            if_exists="replace" if i == 0 else "append",
            index=False,
            method="multi",
            chunksize=1000,
        )
        lignes += len(df)
    return lignes


def main():
    load_dotenv()
    engine = create_engine(os.environ["DATABASE_URL"])

    debut = time.perf_counter()
    with engine.begin() as conn:
        nb_annonces = charger_staging(conn, "annonces", "staging_annonces")
        nb_descripteurs = charger_staging(conn, "descripteurs", "staging_descripteurs")
        conn.execute(text(INSERT_ANNONCES))
        conn.execute(text(INSERT_DESCRIPTEURS))
        total = conn.execute(text("SELECT COUNT(*) FROM annonces")).scalar()
    duree = time.perf_counter() - debut

    logging.info(f"Staging : {nb_annonces} annonces, {nb_descripteurs} descripteurs")
    logging.info(f"Table annonces : {total} lignes, chargement en {duree:.1f} s")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()