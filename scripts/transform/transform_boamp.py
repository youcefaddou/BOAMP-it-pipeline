import json
import logging
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
QUARANTINE_DIR = ROOT / "data" / "quarantine"

COLONNES = [
    "idweb", "objet", "nomacheteur", "code_departement", "dateparution",
    "datelimitereponse", "nature_libelle", "famille_libelle", "type_marche",
    "procedure_libelle", "titulaire", "annonce_lie", "source_schema",
    "url_avis", "descripteur_libelle",
]

def raison_invalide(annonce):
    """Retourne la raison si l'annonce est invalide, sinon None"""
    if not annonce.get("idweb"):
        return "idweb manquant"
    if not annonce.get("dateparution"):
        return "dateparution manquante"
    if not annonce.get("objet"):
        return "objet manquant"
    return None

def premier(valeur):
    """Certains champs de l'API sont des listes (ex: ["35]) : on garde le premier élément """
    if isinstance(valeur, list):
        return valeur[0] if valeur else None
    return valeur

def transformer(annonces):
    """Transforme des annonces brutes en deux DataFrames: annonces et descripteurs"""
    df = pd.DataFrame(annonces, columns=COLONNES)
    df = df.drop_duplicates(subset="idweb", keep="last")
    
    descripteurs = df[["idweb", "descripteur_libelle"]].explode("descripteur_libelle")
    descripteurs = descripteurs.dropna().rename(columns={"descripteur_libelle": "descripteur"})
    
    df = df.drop(columns="descripteur_libelle")
    df["code_departement"] = df["code_departement"].apply(premier)
    df["type_marche"] = df["type_marche"].apply(premier)
    df["titulaire"] = df["titulaire"].apply(lambda t: " ; ".join(t) if isinstance(t, list) else t)
    df["annonce_lie"] = df["annonce_lie"].apply(lambda a: " ; ".join(a) if isinstance(a, list) else a)
    df["objet"] = df["objet"].str.strip()
    df["nomacheteur"] = df["nomacheteur"].str.strip()
    df["dateparution"] = pd.to_datetime(df["dateparution"], errors="coerce")
    df["datelimitereponse"] = pd.to_datetime(df["datelimitereponse"], errors="coerce", utc=True)
    return df, descripteurs

def lire_annee(annee):
    """Lit toutes les années brutes d'une année: c'est le lot"""
    annonces = []
    for chemin in sorted(RAW_DIR.glob(f"boamp_{annee}-*.jsonl")):
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                annonces.append(json.loads(ligne))
    return annonces

def mettre_en_quarantaine(annee, rejets):
    """Ecrit les annonces invalides avec la raison de l'horodatage"""
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    chemin = QUARANTINE_DIR / f"invalid_{annee}_.jsonl"
    with open(chemin, "w", encoding="utf-8") as f:
        for annonce, raison in rejets:
            ligne = {"raison": raison, "horodatage": datetime.now().isoformat(), "donnee": annonce}
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
            
def traiter_annee(annee):
    debut = time.perf_counter()
    brutes = lire_annee(annee)
    
    valides, rejets = [], []
    for annonce in brutes:
        raison = raison_invalide(annonce)
        if raison:
            rejets.append((annonce, raison))
        else:
            valides.append(annonce)
    if rejets:
        mettre_en_quarantaine(annee, rejets)
    
    df, descripteurs = transformer(valides)
    df.to_parquet(PROCESSED_DIR / f"annonces_{annee}.parquet", index=False)
    descripteurs.to_parquet(PROCESSED_DIR / f"descripteurs_{annee}.parquet", index=False)
    
    duree = time.perf_counter() - debut
    logging.info(
        f"{annee} : {len(brutes)} lues, {len(rejets)} en quarantaine, "
        f"{len(df)} annonces écrites en {duree:.1f} s"
    )
    return len(df)

def main():
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    annees = sorted({chemin.name[6:10] for chemin in RAW_DIR.glob("boamp_*.jsonl")})
    total = 0
    for annee in annees:
        total += traiter_annee(annee)
    logging.info(f"{total} annonces transformées sur {len(annees)} années")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    main()