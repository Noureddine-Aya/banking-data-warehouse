import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


load_dotenv()

TEST_DATABASE = "banking_dw_test"


def create_test_engine():
    for name in ("DB_USER", "DB_PASSWORD"):
        if not os.getenv(name):
            raise RuntimeError(f"Variable manquante : {name}")

    url = URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=TEST_DATABASE,
    )

    return create_engine(url, pool_pre_ping=True)


write_engine = create_test_engine()


def verify_test_database(connection):
    database = connection.execute(
        text("SELECT current_database()")
    ).scalar_one()

    if database != TEST_DATABASE:
        raise RuntimeError(
            "Connexion refusée : banking_dw_test est obligatoire."
        )

    return database


def check_write_connection():
    """Vérifier la connexion par une lecture uniquement."""

    try:
        with write_engine.connect() as connection:
            with connection.begin():
                connection.execute(
                    text("SET TRANSACTION READ ONLY")
                )

                database = verify_test_database(connection)

                print(f"Base de données : {database}")
                print("Connexion de test vérifiée.")
                print("Aucune donnée modifiée.")
    finally:
        write_engine.dispose()


if __name__ == "__main__":
    check_write_connection()