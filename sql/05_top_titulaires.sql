-- Entreprises qui remportent le plus de marchés IT et télécoms
WITH resultats_it AS (
    SELECT DISTINCT a.idweb, a.titulaire
    FROM annonces a
    JOIN annonce_descripteurs d ON d.idweb = a.idweb
    WHERE a.nature_libelle = 'Résultat de marché'
      AND a.titulaire IS NOT NULL
      AND d.descripteur IN (
          'Logiciel',
          'Informatique (prestations de services)',
          'Informatique (matériel)',
          'Informatique (maintenance serveurs et réseaux)',
          'Télécommunications'
      )
)
SELECT
    titulaire,
    COUNT(*) AS nb_marches,
    RANK() OVER (ORDER BY COUNT(*) DESC) AS rang
FROM resultats_it
GROUP BY titulaire
ORDER BY rang, titulaire
LIMIT 20;