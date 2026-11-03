-- Nombre d'annonces IT par année et par nature d'avis
SELECT
    EXTRACT(YEAR FROM dateparution)::int AS annee,
    nature_libelle,
    COUNT(*) AS nb_annonces
FROM annonces
GROUP BY annee, nature_libelle
ORDER BY annee, nb_annonces DESC;