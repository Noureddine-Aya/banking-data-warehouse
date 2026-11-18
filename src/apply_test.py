
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import create_engine, text

from test_db_connection import test_url


def apply_test_update():
    engine = create_engine(test_url, pool_pre_ping=True)

    with engine.begin() as conn:
        database = conn.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if database != "banking_dw_test":
            raise RuntimeError(
                "Sécurité : la base connectée n'est pas banking_dw_test."
            )

        value = Decimal("2.825").quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        result = conn.execute(
            text("""
                UPDATE dw.dim_district_etl_test
                SET unemployment_95 = :value
                WHERE district_id = 69
                  AND unemployment_95 IS NULL
            """),
            {"value": value}
        )

        print(f"Base : {database}")
        print(f"Lignes modifiées : {result.rowcount}")

        updated_value = conn.execute(
            text("""
                SELECT unemployment_95
                FROM dw.dim_district_etl_test
                WHERE district_id = 69
            """)
        ).scalar_one()

        if updated_value != Decimal("2.83"):
            raise RuntimeError(
                "Validation échouée : transaction annulée."
            )

        print(f"Nouvelle valeur : {updated_value}")
        print("Transaction validée automatiquement.")

    engine.dispose()


if __name__ == "__main__":
    apply_test_update()
