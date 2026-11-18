
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

test_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database="banking_dw_test",
)

test_engine = create_engine(test_url, pool_pre_ping=True)

with test_engine.connect() as conn:
    database = conn.execute(
        text("SELECT current_database()")
    ).scalar_one()

    rows = conn.execute(
        text("""
            SELECT district_id, district_name, unemployment_95
            FROM dw.dim_district_etl_test
            ORDER BY district_id
        """)
    ).fetchall()

    print(f"Base connectée : {database}")
    print(f"Nombre de districts : {len(rows)}")

    for row in rows:
        print(row)

    assert database == "banking_dw_test"
    assert len(rows) == 2

print("\nConnexion de test validée.")
print("Aucune donnée PostgreSQL modifiée.")
