
import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

db_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "banking_dw"),
)

engine = create_engine(
    db_url,
    connect_args={
        "options": "-c default_transaction_read_only=on"
    },
)


def extract_districts():
    """Extraire les districts depuis PostgreSQL."""

    query = text("SELECT * FROM staging.district ORDER BY district_id")

    with engine.connect() as connection:
        df = pd.read_sql_query(query, connection)

    print("Extraction terminée !")
    print(f"Nombre de lignes : {len(df)}")
    print(f"Nombre de colonnes : {len(df.columns)}")

    print("\nAperçu des données :")
    print(df.head())

    print("\nValeurs manquantes :")
    print(df.isnull().sum())

    print("\nDoublons de district_id :")
    print(df["district_id"].duplicated().sum())

    return df


if __name__ == "__main__":
    extract_districts()
