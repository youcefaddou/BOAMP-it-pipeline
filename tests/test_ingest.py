from datetime import date

from ingest_boamp import (
    charger_checkpoint,
    construire_where,
    est_retentable,
    liste_mois,
    mois_suivant,
    sauver_checkpoint,
)
def test_liste_mois():
    resultat = liste_mois(date(2020, 11, 1), date(2021, 2, 15))
    assert resultat == ["2020-11", "2020-12", "2021-01", "2021-02"]
    
def test_mois_suivant_decembre():
    assert mois_suivant("2020-12") == "2021-01"
    
def test_construire_where():
    where = construire_where("2020-01")
    assert "date'2020-01-01'" in where
    assert "date'2020-02-01'" in where
    assert 'descripteur_libelle="Logiciel"' in where
    
def test_est_retentable():
    assert est_retentable(429)
    assert est_retentable(503)
    assert not est_retentable(404)
    assert not est_retentable(400)
    
def test_checkpoint(tmp_path):
    chemin = tmp_path / "checkpoint.json"
    assert charger_checkpoint(chemin) == set()
    sauver_checkpoint(chemin, {"2020-02", "2020-01"})
    assert charger_checkpoint(chemin) == {"2020-01", "2020-02"}