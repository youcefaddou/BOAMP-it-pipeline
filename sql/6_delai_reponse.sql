-- Délai moyen de réponse (jours entre parution et date limitz) par famille de marché
SELECT
    famille_libelle,
    COUNT(*) AS nb_avis,
    ROUND(AVG(datelimitereponse::date - dateparution), 1) AS delai_moyen_jours
FROM annonces
WHERE nature_libelle = 'Avis de marché'
  AND datelimitereponse IS NOT NULL
GROUP BY famille_libelle
ORDER BY delai_moyen_jours DESC;