import asyncio
import json
import logging
import random
import time
from datetime import date
from pathlib import Path

import aiohttp

from config import BASE_URL, DATE_DEBUT, DESCRIPTEURS_IT, PAGE_SIZE

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
CHECKPOINT = RAW_DIR / "checkpoint.json"
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
NB_REQUETES_MAX = 5
NB_TENTATIVES_MAX = 5
STATUS_A_REESSAYER = {429, 500, 502, 503, 504}

class SourceIndisponible(Exception):
    """Erreur temporaire de l'API: la requete peut etre retentée"""

def est_retentable(statut):
    return statut in STATUS_A_REESSAYER


def liste_mois(debut, fin):
    """Retourne la liste des mois entre debut et fin, au format AAAA-MM"""
    mois = []
    annee, m = debut.year, debut.month
    while (annee, m) <= (fin.year, fin.month):
        mois.append(f"{annee}-{m:02d}")
        m += 1
        if m == 13:
            annee, m = annee + 1, 1
    return mois
        
def mois_suivant(mois):
    annee, m = map(int, mois.split("-"))
    if m == 12:
        return f"{annee + 1}-01"
    return f"{annee}-{m + 1:02d}"

def construire_where(mois):
    """Filtre de l'API: annonces IT pubbliées pendant le mois donné"""
    descripteurs = " OR ".join(f'descripteur_libelle="{d}"' for d in DESCRIPTEURS_IT)
    return (
        f"dateparution >= date'{mois}-01' "
        f"AND dateparution < date'{mois_suivant(mois)}-01' "
        f"AND ({descripteurs})"
    )

async def recuperer_page(session, semaphore, mois, offset):
    """Recupere une page de 100 annonces, avec retries en cas d'erreur temporaire"""
    params = {
        "where": construire_where(mois),
        "limit": PAGE_SIZE,
        "offset": offset,
        "order_by": "idweb",
    }
    for tentative in range(1, NB_TENTATIVES_MAX + 1):
        try:
            async with semaphore:
                async with session.get(BASE_URL, params=params) as reponse:
                    if est_retentable(reponse.status):
                        raise SourceIndisponible(f"HTTP {reponse.status}")
                    reponse.raise_for_status()
                    return await reponse.json()
        except (SourceIndisponible, asyncio.TimeoutError, aiohttp.ClientConnectionError) as erreur:
            if tentative == NB_TENTATIVES_MAX:
                raise
            delai = 2 ** tentative + random.uniform(0, 1)
            logging.warning("%s offset %s : %s, nouvel essai dans %.1f s", mois, offset, erreur, delai)
            await asyncio.sleep(delai)
        
        
def ecrire_page(mois, numero_page, annonces):
    """Ecrit iune page d'annonces dans un fichier JSON Lines"""
    chemin = RAW_DIR / f"boamp_{mois}_p{numero_page:03d}.jsonl"
    with open(chemin, "w", encoding="utf-8") as f:
        for annonce in annonces:
            f.write(json.dumps(annonce, ensure_ascii=False) + "\n")

def charger_checkpoint(chemin):
    """Retourne l'ensemble des mois deja collectés"""
    if not chemin.exists():
        return set()
    with open(chemin, encoding="utf-8") as f:
        return set(json.load(f))
    
def sauver_checkpoint(chemin, mois_termines):
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(sorted(mois_termines), f, indent=2)

async def collecter_mois(session, semaphore, mois):
    """Collecte toutes les pages d'un mois et retourne le nombre d'annocnes"""
    premiere_page = await recuperer_page(session, semaphore, mois, 0)
    total = premiere_page["total_count"]
    if total == 0:
        return 0
    ecrire_page(mois, 0, premiere_page["results"])
    
    offsets = range(PAGE_SIZE, total, PAGE_SIZE)
    pages = await asyncio.gather(*[recuperer_page(session, semaphore, mois, offset) for offset in offsets])
    for numero, page in enumerate(pages, start=1):
        ecrire_page(mois, numero, page["results"])
    logging.info(f"{mois} : {total} annonces")
    return total

def configurer_logs():
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOG_DIR / "ingest.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

async def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tous_les_mois = liste_mois(date.fromisoformat(DATE_DEBUT), date.today())
    mois_en_cours = date.today().strftime("%Y-%m")

    mois_termines = charger_checkpoint(CHECKPOINT)
    a_collecter = [m for m in tous_les_mois if m not in mois_termines]
    logging.info(f"{len(a_collecter)} mois à collecter, {len(mois_termines)} déjà faits")
    timeout = aiohttp.ClientTimeout(total=30, connect=5)
    connecteur = aiohttp.TCPConnector(limit=NB_REQUETES_MAX)
    semaphore = asyncio.Semaphore(NB_REQUETES_MAX)

    debut = time.perf_counter()
    async with aiohttp.ClientSession(timeout=timeout, connector=connecteur) as session:
        resultats = await asyncio.gather(
            *[collecter_mois(session, semaphore, mois) for mois in a_collecter],
            return_exceptions=True,
        )
    duree = time.perf_counter() - debut

    total = 0
    for mois, resultat in zip(a_collecter, resultats):
        if isinstance(resultat, BaseException):
            logging.error(f"{mois} : échec ({resultat})")
        else:
            total += resultat
            if mois != mois_en_cours:
                mois_termines.add(mois)
    sauver_checkpoint(CHECKPOINT, mois_termines)
    logging.info(f"{total} annonces collectées sur {len(a_collecter)} mois en {duree:.1f} s")

if __name__ == "__main__":
    configurer_logs()
    asyncio.run(main())