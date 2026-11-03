from transform_boamp import raison_invalide, transformer


def annonce(idweb, objet="Achat de licences"):
    return {
        "idweb": idweb,
        "objet": objet,
        "dateparution": "2024-01-15",
        "nomacheteur": " Mairie ",
        "code_departement": ["13"],
        "type_marche": ["SERVICES"],
        "descripteur_libelle": ["Logiciel", "Informatique (matériel)"],
        "titulaire": None,
    }


def test_raison_invalide():
    assert raison_invalide(annonce("24-1")) is None
    assert raison_invalide(annonce("24-1", objet="")) == "objet manquant"
    assert raison_invalide({"objet": "x"}) == "idweb manquant"


def test_dedoublonnage_garde_la_derniere_version():
    df, _ = transformer([annonce("24-1", objet="v1"), annonce("24-1", objet="v2")])
    assert len(df) == 1
    assert df.iloc[0]["objet"] == "v2"


def test_descripteurs_et_champs_listes():
    df, descripteurs = transformer([annonce("24-1")])
    assert len(descripteurs) == 2
    assert df.iloc[0]["code_departement"] == "13"
    assert df.iloc[0]["nomacheteur"] == "Mairie"
    
def test_annonce_lie_liste_devient_texte():
    brute = annonce("24-1")
    brute["annonce_lie"] = ["23-100", "23-200"]
    df, _ = transformer([brute])
    assert df.iloc[0]["annonce_lie"] == "23-100 ; 23-200"    