-- Volume mensuel des transactions.
-- Les montants sont ceux du jeu de données transformé.

SELECT
    d.year AS annee,
    d.month AS mois,
    COUNT(*) AS nombre_transactions,
    COUNT(*) FILTER (
        WHERE f.amount IS NULL
    ) AS montants_manquants,
    SUM(f.amount) AS montant_total
FROM dw.fact_transactions f
JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- Repartition des prets par code de statut.
SELECT
    loan_status AS statut,
    COUNT(*) AS nombre_prets,
    COUNT(*) FILTER (
        WHERE loan_amount IS NULL
    ) AS montants_manquants,
    SUM(loan_amount) AS montant_total_prets,
    ROUND(AVG(loan_amount), 2) AS montant_moyen_pret,
    ROUND(AVG(duration_months), 1) AS duree_moyenne_mois
FROM dw.fact_loans
GROUP BY loan_status
ORDER BY loan_status;