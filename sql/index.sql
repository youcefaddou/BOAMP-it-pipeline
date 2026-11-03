-- Index justifié par EXPLAIN ANALYZE sur la requête 07 (voir README)
CREATE INDEX IF NOT EXISTS idx_annonces_nature_date
    ON annonces (nature_libelle, dateparution);

ANALYZE annonces;