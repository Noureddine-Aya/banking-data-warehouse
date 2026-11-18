import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


CHECKS = {
    "Opérations NULL": """
        SELECT COUNT(*) FROM staging.trans
        WHERE operation IS NULL
    """,
    "Opérations vides ou espaces": """
        SELECT COUNT(*) FROM staging.trans
        WHERE operation IS NOT NULL AND BTRIM(operation) = ''
    """,
    "Codes non vides absents de dim_operation": """
        SELECT COUNT(*)
        FROM staging.trans t
        WHERE NULLIF(BTRIM(t.operation), '') IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM dw.dim_operation d
              WHERE d.operation_code = BTRIM(t.operation)
          )
    """,
    "Lignes UNKNOWN marquées inconnues (attendu : 1)": """
        SELECT COUNT(*) FROM dw.dim_operation
        WHERE operation_code = 'UNKNOWN' AND is_unknown
    """,
    "Prêts sans compte source valide": """
        SELECT COUNT(*) FROM staging.loan s
        WHERE NOT EXISTS (
            SELECT 1 FROM staging.account a
            WHERE a.account_id = s.account_id
        )
    """,
    "Ordres sans compte source valide": """
        SELECT COUNT(*) FROM staging.payment_order s
        WHERE NOT EXISTS (
            SELECT 1 FROM staging.account a
            WHERE a.account_id = s.account_id
        )
    """,
    "Transactions sans compte source valide": """
        SELECT COUNT(*) FROM staging.trans s
        WHERE NOT EXISTS (
            SELECT 1 FROM staging.account a
            WHERE a.account_id = s.account_id
        )
    """,
    "Prêts sans date": """
        SELECT COUNT(*) FROM staging.loan WHERE date IS NULL
    """,
    "Transactions sans date": """
        SELECT COUNT(*) FROM staging.trans WHERE date IS NULL
    """,
    "Dates de faits absentes de dim_date": """
        WITH source_dates AS (
            SELECT date FROM staging.loan WHERE date IS NOT NULL
            UNION
            SELECT date FROM staging.trans WHERE date IS NOT NULL
        )
        SELECT COUNT(*) FROM source_dates s
        WHERE NOT EXISTS (
            SELECT 1 FROM dw.dim_date d WHERE d.full_date = s.date
        )
    """,
    "Dates incompatibles avec les conventions observées": """
        SELECT COUNT(*) FROM dw.dim_date
        WHERE date_key IS DISTINCT FROM
                  TO_CHAR(full_date, 'YYYYMMDD')::integer
           OR year IS DISTINCT FROM EXTRACT(YEAR FROM full_date)::integer
           OR quarter IS DISTINCT FROM EXTRACT(QUARTER FROM full_date)::integer
           OR month IS DISTINCT FROM EXTRACT(MONTH FROM full_date)::integer
           OR day IS DISTINCT FROM EXTRACT(DAY FROM full_date)::integer
           OR day_of_week IS DISTINCT FROM
                  EXTRACT(ISODOW FROM full_date)::integer
           OR is_weekend IS DISTINCT FROM
                  (EXTRACT(ISODOW FROM full_date) IN (6, 7))
    """,
}


def main():
    load_dotenv()

    for name in ("DB_USER", "DB_PASSWORD"):
        if not os.getenv(name):
            raise RuntimeError(f"Variable manquante : {name}")

    url = URL.create(
        "postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database="banking_dw",
    )

    engine = create_engine(url, pool_pre_ping=True, echo=False)

    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text(
                    "SET TRANSACTION ISOLATION LEVEL "
                    "REPEATABLE READ, READ ONLY"
                ))
                conn.execute(text("SET LOCAL statement_timeout = '60s'"))

                database = conn.execute(
                    text("SELECT current_database()")
                ).scalar_one()

                if database != "banking_dw":
                    raise RuntimeError("Base incorrecte : audit arrêté.")

                print(f"Base : {database} — lecture seule\n")

                anomalies = []

                for label, sql in CHECKS.items():
                    count = conn.execute(text(sql)).scalar_one()
                    print(f"{label} : {count}")

                    if label in (
                        "Opérations NULL",
                        "Opérations vides ou espaces",
                    ):
                        # Ces opérations seront rattachées à UNKNOWN.
                        continue

                    expected = (
                        1
                        if label == (
                            "Lignes UNKNOWN marquées inconnues "
                            "(attendu : 1)"
                        )
                        else 0
                    )

                    if count != expected:
                        anomalies.append(
                            f"{label} : {count}, attendu : {expected}"
                        )

                if anomalies:
                    raise RuntimeError(
                        "Audit bloquant :\n" + "\n".join(anomalies)
                    )

        print("\nAudit terminé. Aucune donnée modifiée.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()