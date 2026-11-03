CREATE TABLE IF NOT EXISTS annonces (
    idweb              TEXT PRIMARY KEY,
    objet              TEXT NOT NULL,
    nomacheteur        TEXT,
    code_departement   VARCHAR(3),
    dateparution       DATE NOT NULL,
    datelimitereponse  TIMESTAMPTZ,
    nature_libelle     TEXT,
    famille_libelle    TEXT,
    type_marche        TEXT CHECK (type_marche IN ('SERVICES', 'FOURNITURES', 'TRAVAUX')),
    procedure_libelle  TEXT,
    titulaire          TEXT,
    annonce_lie        TEXT,
    source_schema      TEXT,
    url_avis           TEXT
);

-- Une annonce peut avoir plusieurs descripteurs (relation 1:N)
CREATE TABLE IF NOT EXISTS annonce_descripteurs (
    idweb        TEXT NOT NULL REFERENCES annonces (idweb) ON DELETE CASCADE,
    descripteur  TEXT NOT NULL,
    PRIMARY KEY (idweb, descripteur)
);