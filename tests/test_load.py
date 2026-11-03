import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
pytestmark = pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="pas de base config")

def compter_annonces(engine):
    with engine.connect() as conn:
        return conn.execute(text("SELECT COUNT(*) FROM annonces")).scalar()


def test_chargement_rejouable_sans_doublons():
    from load_boamp import main

    engine = create_engine(os.environ["DATABASE_URL"])
    main()
    avant = compter_annonces(engine)
    main()
    assert compter_annonces(engine) == avant
