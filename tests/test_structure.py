from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOSSIERS = ["sql", "scripts/ingest", "scripts/transform", "data/raw", "data/processed", "tests" ]

def test_structure():
    for dossier in DOSSIERS:
        assert (ROOT / dossier).is_dir(), f"Le dossier {dossier} est manquant"
