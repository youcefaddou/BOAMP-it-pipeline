-- Top 5 des acheteurs par année (nbre d'avis de marché publiés)
WITH achats AS (
    SELECT
        EXTRACT(YEAR FROM dateparution)::int AS annee,
        nomacheteur,
        COUNT(*) AS nb_avis
    FROM annonces
    WHERE nature_libelle = 'Avis de marché'
    GROUP BY annee, nomacheteur
),
classement AS (
    SELECT
        annee,
        nomacheteur,
        nb_avis,
        ROW_NUMBER() OVER (PARTITION BY annee ORDER BY nb_avis DESC, nomacheteur) AS rang
    FROM achats
)
SELECT annee, rang, nomacheteur, nb_avis
FROM classement
WHERE rang <= 5
ORDER BY annee, rang;