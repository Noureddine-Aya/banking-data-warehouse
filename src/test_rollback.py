
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from dotenv import load_dotenv
import os

load_dotenv()

test_url = URL.create(
    "postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database="banking_dw_test",
)

engine = create_engine(test_url, pool_pre_ping=True)

try:
    with engine.begin() as conn:
        db_name = conn.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if db_name != "banking_dw_test":
            raise RuntimeError("Base de test incorrecte.")

        conn.execute(
            text("""
                UPDATE dw.dim_district_etl_test
                SET unemployment_95 = 9.99
                WHERE district_id = 69
            """)
        )

        print("Modification temporaire effectuée.")

        # Simulation d'une erreur pendant le chargement
        raise RuntimeError("Erreur ETL simulée")

except RuntimeError as error:
    print(f"Erreur interceptée : {error}")
    print("Rollback automatique demandé.")

with engine.connect() as conn:
    final_value = conn.execute(
        text("""
            SELECT unemployment_95
            FROM dw.dim_district_etl_test
            WHERE district_id = 69
        """)
    ).scalar_one()

    print(f"Valeur après rollback : {final_value}")

    assert str(final_value) == "2.83", (
        "Échec : la valeur initiale n'a pas été conservée."
    )

print("TEST ROLLBACK RÉUSSI")
engine.dispose()
