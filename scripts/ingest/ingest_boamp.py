import asyncio
import json
import time
from datetime import date
from pathlib import Path

import aiohttp

from config import BASE_URL, DATE_DEBUT, DESCRIPTEURS_IT, PAGE_SIZE

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
NB_REQUETES_MAX = 5

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
    """Recupere une page de 100 annonces pour un mois donné"""
    params = {
        "where": construire_where(mois),
        "limit": PAGE_SIZE,
        "offset": offset,
        "order_by": "idweb",
    }
    async with semaphore:
        async with session.get(BASE_URL, params=params) as response:
            response.raise_for_status()
            return await response.json()
        
        
def ecrire_page(mois, numero_page, annonces):
    """Ecrit iune page d'annonces dans un fichier JSON Lines"""
    chemin = RAW_DIR / f"boamp_{mois}_p{numero_page:03d}.jsonl"
    with open(chemin, "w", encoding="utf-8") as f:
        for annonce in annonces:
            f.write(json.dumps(annonce, ensure_ascii=False) + "\n")
            

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
    return total
async def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tous_les_mois = liste_mois(date.fromisoformat(DATE_DEBUT), date.today())

    timeout = aiohttp.ClientTimeout(total=30, connect=5)
    connecteur = aiohttp.TCPConnector(limit=NB_REQUETES_MAX)
    semaphore = asyncio.Semaphore(NB_REQUETES_MAX)

    debut = time.perf_counter()
    async with aiohttp.ClientSession(timeout=timeout, connector=connecteur) as session:
        resultats = await asyncio.gather(
            *[collecter_mois(session, semaphore, mois) for mois in tous_les_mois],
            return_exceptions=True,
        )
    duree = time.perf_counter() - debut

    total = 0
    for mois, resultat in zip(tous_les_mois, resultats):
        if isinstance(resultat, Exception):
            print(f"{mois} : échec ({resultat})")
        else:
            total += resultat
    print(f"{total} annonces collectées sur {len(tous_les_mois)} mois en {duree:.1f} s")


if __name__ == "__main__":
    asyncio.run(main())