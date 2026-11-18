from sqlalchemy import text

from extract import engine


QUERIES = {
    "dim_account": """
        SELECT
            COUNT(*) FILTER (
                WHERE d.account_id IS NULL
            ) AS nouvelles,
            COUNT(*) FILTER (
                WHERE d.account_id IS NOT NULL
                  AND ROW(
                      s.district_id,
                      s.date,
                      s.frequency
                  ) IS DISTINCT FROM ROW(
                      d.district_id,
                      d.opening_date,
                      d.statement_frequency
                  )
            ) AS differentes
        FROM staging.account s
        LEFT JOIN dw.dim_account d
            ON d.account_id = s.account_id
    """,

    "dim_client": """
        SELECT
            COUNT(*) FILTER (
                WHERE d.client_id IS NULL
            ) AS nouvelles,
            COUNT(*) FILTER (
                WHERE d.client_id IS NOT NULL
                  AND ROW(
                      s.birth_date,
                      s.gender,
                      s.district_id
                  ) IS DISTINCT FROM ROW(
                      d.birth_date,
                      d.gender,
                      d.district_id
                  )
            ) AS differentes
        FROM staging.client s
        LEFT JOIN dw.dim_client d
            ON d.client_id = s.client_id
    """,

    "fact_loans": """
        SELECT
            COUNT(*) FILTER (
                WHERE f.loan_id IS NULL
            ) AS nouvelles,
            COUNT(*) FILTER (
                WHERE f.loan_id IS NOT NULL
                  AND ROW(
                      f.account_key,
                      f.date_key,
                      f.loan_amount,
                      f.duration_months,
                      f.monthly_payment,
                      f.loan_status
                  ) IS DISTINCT FROM ROW(
                      a.account_key,
                      d.date_key,
                      s.amount,
                      s.duration,
                      s.payments,
                      s.status
                  )
            ) AS differentes,
            COUNT(*) FILTER (
                WHERE a.account_key IS NULL
                   OR d.date_key IS NULL
            ) AS references_manquantes
        FROM staging.loan s
        LEFT JOIN dw.dim_account a
            ON a.account_id = s.account_id
        LEFT JOIN dw.dim_date d
            ON d.full_date = s.date
        LEFT JOIN dw.fact_loans f
            ON f.loan_id = s.loan_id
    """,
}

QUERIES.update({
    "fact_payment_orders": """
        SELECT
            COUNT(*) FILTER (
                WHERE f.order_id IS NULL
            ) AS nouvelles,
            COUNT(*) FILTER (
                WHERE f.order_id IS NOT NULL
                  AND ROW(
                      f.account_key,
                      f.bank_to,
                      f.account_to,
                      f.amount,
                      f.k_symbol
                  ) IS DISTINCT FROM ROW(
                      a.account_key,
                      s.bank_to,
                      s.account_to,
                      s.amount,
                      s.k_symbol
                  )
            ) AS differentes,
            COUNT(*) FILTER (
                WHERE a.account_key IS NULL
            ) AS references_manquantes
        FROM staging.payment_order s
        LEFT JOIN dw.dim_account a
            ON a.account_id = s.account_id
        LEFT JOIN dw.fact_payment_orders f
            ON f.order_id = s.order_id
    """,

    "fact_transactions": """
        SELECT
            COUNT(*) FILTER (
                WHERE f.transaction_id IS NULL
            ) AS nouvelles,
            COUNT(*) FILTER (
                WHERE f.transaction_id IS NOT NULL
                  AND ROW(
                      f.account_key,
                      f.date_key,
                      f.operation_key,
                      f.transaction_type,
                      f.amount,
                      f.balance,
                      f.k_symbol
                  ) IS DISTINCT FROM ROW(
                      a.account_key,
                      d.date_key,
                      o.operation_key,
                      s.type,
                      s.amount,
                      s.balance,
                      s.k_symbol
                  )
            ) AS differentes,
            COUNT(*) FILTER (
                WHERE a.account_key IS NULL
                   OR d.date_key IS NULL
                   OR o.operation_key IS NULL
            ) AS references_manquantes
        FROM staging.trans s
        LEFT JOIN dw.dim_account a
            ON a.account_id = s.account_id
        LEFT JOIN dw.dim_date d
            ON d.full_date = s.date
        LEFT JOIN dw.dim_operation o
            ON o.operation_code = COALESCE(
                NULLIF(BTRIM(s.operation), ''),
                'UNKNOWN'
            )
        LEFT JOIN dw.fact_transactions f
            ON f.transaction_id = s.trans_id
    """,
})

QUERIES["dim_district"] = """
    SELECT
        COUNT(*) FILTER (
            WHERE d.district_id IS NULL
        ) AS nouvelles,
        COUNT(*) FILTER (
            WHERE d.district_id IS NOT NULL
              AND ROW(
                  s.district_name,
                  s.region,
                  s.inhabitants,
                  s.urban_ratio,
                  s.salary,
                  COALESCE(
                      s.unemployment_95,
                      d.unemployment_95
                  ),
                  s.unemployment_96,
                  s.entrepreneurs
              ) IS DISTINCT FROM ROW(
                  d.district_name,
                  d.region,
                  d.inhabitants,
                  d.urban_ratio,
                  d.average_salary,
                  d.unemployment_95,
                  d.unemployment_96,
                  d.entrepreneurs
              )
        ) AS differentes
    FROM staging.district s
    LEFT JOIN dw.dim_district d
        ON d.district_id = s.district_id
"""
QUERIES["dim_date"] = """
    WITH required_dates AS (
        SELECT date AS full_date
        FROM staging.loan
        WHERE date IS NOT NULL

        UNION

        SELECT date
        FROM staging.trans
        WHERE date IS NOT NULL
    )
    SELECT
        COUNT(*) FILTER (
            WHERE d.full_date IS NULL
        ) AS nouvelles,
        COUNT(*) FILTER (
            WHERE d.full_date IS NOT NULL
              AND ROW(
                  d.date_key,
                  d.year,
                  d.quarter,
                  d.month,
                  d.day,
                  d.day_of_week,
                  d.is_weekend
              ) IS DISTINCT FROM ROW(
                  TO_CHAR(s.full_date, 'YYYYMMDD')::integer,
                  EXTRACT(YEAR FROM s.full_date)::integer,
                  EXTRACT(QUARTER FROM s.full_date)::integer,
                  EXTRACT(MONTH FROM s.full_date)::integer,
                  EXTRACT(DAY FROM s.full_date)::integer,
                  EXTRACT(ISODOW FROM s.full_date)::integer,
                  EXTRACT(ISODOW FROM s.full_date) IN (6, 7)
              )
        ) AS differentes
    FROM required_dates s
    LEFT JOIN dw.dim_date d
        ON d.full_date = s.full_date
"""
QUERIES["dim_operation"] = """
    WITH required_operations AS (
        SELECT DISTINCT
            COALESCE(
                NULLIF(BTRIM(operation), ''),
                'UNKNOWN'
            ) AS operation_code
        FROM staging.trans

        UNION

        SELECT 'UNKNOWN'
    )
    SELECT
        COUNT(*) FILTER (
            WHERE d.operation_code IS NULL
        ) AS nouvelles,
        COUNT(*) FILTER (
            WHERE d.operation_code IS NOT NULL
              AND (
                  d.is_unknown IS DISTINCT FROM
                      (s.operation_code = 'UNKNOWN')
                  OR NULLIF(
                      BTRIM(d.operation_label), ''
                  ) IS NULL
              )
        ) AS differentes
    FROM required_operations s
    LEFT JOIN dw.dim_operation d
        ON d.operation_code = s.operation_code
"""

def compare_dimensions():
    """Comparer les comptes, clients et prêts sans modifier la base."""

    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(
                "SET TRANSACTION ISOLATION LEVEL "
                "REPEATABLE READ, READ ONLY"
            ))

            conn.execute(text(
                "SET LOCAL statement_timeout = '60s'"
            ))

            database = conn.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if database != "banking_dw":
                raise RuntimeError(
                    "Base incorrecte : comparaison arrêtée."
                )

            print(f"\nBase : {database} — lecture seule")
            print("COMPARAISON DES COMPTES, CLIENTS ET PRETS")
            print("-" * 55)

            for table, sql in QUERIES.items():
                row = conn.execute(text(sql)).mappings().one()

                missing_references = row.get(
                    "references_manquantes", 0
                )

                if missing_references != 0:
                    raise RuntimeError(
                        f"{table} : {missing_references} références "
                        "manquantes, comparaison arrêtée."
                    )

                print(
                    f"{table} : "
                    f"{row['nouvelles']} nouvelles lignes, "
                    f"{row['differentes']} lignes différentes"
                )

    print("\nComparaison terminée. Aucune donnée modifiée.")


if __name__ == "__main__":
    compare_dimensions()