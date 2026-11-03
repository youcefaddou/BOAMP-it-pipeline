-- Les 15 descripteurs les plus fréquents dans les avis de marché avec leur part
SELECT
    d.descripteur,
    COUNT(*) AS nb_annonces,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS part_pct
FROM annonce_descripteurs d
JOIN annonces a ON a.idweb = d.idweb
WHERE a.nature_libelle = 'Avis de marché'
GROUP BY d.descripteur
ORDER BY nb_annonces DESC
LIMIT 15;