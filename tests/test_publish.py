from publish_hub import construire_card

def test_card_contient_licence_et_langue():
    contenu = str(construire_card())
    assert "license: other" in contenu
    assert "Licence Ouverte" in contenu
    assert "language: fr" in contenu