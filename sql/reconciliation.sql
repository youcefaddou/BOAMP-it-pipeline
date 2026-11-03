-- Réconciliation : annonces présentes d'un seul côté (srce = staging, cible = annonces)
SELECT
    COALESCE(s.idweb, c.idweb) AS idweb,
    CASE
        WHEN s.idweb IS NULL THEN 'absent de la source'
        WHEN c.idweb IS NULL THEN 'absent de la cible'
    END AS statut
FROM staging_annonces s
FULL JOIN annonces c ON s.idweb = c.idweb
WHERE s.idweb IS NULL OR c.idweb IS NULL;