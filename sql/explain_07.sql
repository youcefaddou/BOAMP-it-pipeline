EXPLAIN (ANALYZE, BUFFERS)
SELECT DISTINCT a.nomacheteur
FROM annonces a
WHERE a.nature_libelle = 'Avis de marché'
  AND a.dateparution >= DATE '2024-01-01'
  AND a.dateparution < DATE '2025-01-01'
  AND NOT EXISTS (
      SELECT 1
      FROM annonces b
      WHERE b.nomacheteur = a.nomacheteur
        AND b.nature_libelle = 'Avis de marché'
        AND b.dateparution >= DATE '2025-01-01'
        AND b.dateparution < DATE '2026-01-01'
  );