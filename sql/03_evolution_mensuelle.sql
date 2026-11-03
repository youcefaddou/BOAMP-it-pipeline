-- Avis de marché par mois, moyenne mobile sur 12 mois et variation d'un mois sur l'autre
WITH mois AS (
    SELECT generate_series(
        DATE '2015-03-01',
        date_trunc('month', CURRENT_DATE)::date,
        INTERVAL '1 month'
    )::date AS mois
),
volumes AS (
    SELECT date_trunc('month', dateparution)::date AS mois, COUNT(*) AS nb
    FROM annonces
    WHERE nature_libelle = 'Avis de marché'
    GROUP BY 1
)
SELECT
    m.mois,
    COALESCE(v.nb, 0) AS nb_avis,
    ROUND(AVG(COALESCE(v.nb, 0)) OVER (
        ORDER BY m.mois ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
    ), 1) AS moyenne_mobile_12_mois,
    COALESCE(v.nb, 0) - LAG(COALESCE(v.nb, 0)) OVER (ORDER BY m.mois) AS variation
FROM mois m
LEFT JOIN volumes v ON v.mois = m.mois
ORDER BY m.mois;