from sqlalchemy import text

from db_writer import write_engine, verify_test_database
from etl_banking_test import JOBS, check_sources, run_job


class ErreurSimulee(Exception):
    pass


def lire_pret(conn, loan_id):
    return conn.execute(
        text("""
            SELECT
                s.amount AS montant_source,
                f.loan_amount AS montant_dw
            FROM staging.loan s
            JOIN dw.fact_loans f ON f.loan_id = s.loan_id
            WHERE s.loan_id = :loan_id
        """),
        {"loan_id": loan_id},
    ).one()


def main():
    try:
        # Lecture de l'état initial.
        with write_engine.connect() as conn:
            with conn.begin():
                conn.execute(text("SET TRANSACTION READ ONLY"))
                verify_test_database(conn)

                loan_id = conn.execute(text("""
                    SELECT s.loan_id
                    FROM staging.loan s
                    JOIN dw.fact_loans f ON f.loan_id = s.loan_id
                    WHERE s.amount IS NOT NULL
                      AND s.amount = f.loan_amount
                      AND s.amount < 9999999999998
                    ORDER BY s.loan_id
                    LIMIT 1
                """)).scalar_one()

                initial = tuple(lire_pret(conn, loan_id))

        print(f"Prêt testé : {loan_id}")
        print(f"Montant initial : {initial[0]}")

        try:
            with write_engine.begin() as conn:
                verify_test_database(conn)
                conn.execute(text(
                    "SET LOCAL statement_timeout = '180s'"
                ))
                conn.execute(text(
                    "SET LOCAL lock_timeout = '10s'"
                ))

                # Verrouiller le prêt pendant le test.
                conn.execute(
                    text("""
                        SELECT loan_id
                        FROM staging.loan
                        WHERE loan_id = :loan_id
                        FOR UPDATE
                    """),
                    {"loan_id": loan_id},
                ).scalar_one()

                if tuple(lire_pret(conn, loan_id)) != initial:
                    raise RuntimeError(
                        "Les données ont changé. Test arrêté."
                    )

                conn.execute(
                    text("""
                        UPDATE staging.loan
                        SET amount = amount + 1
                        WHERE loan_id = :loan_id
                    """),
                    {"loan_id": loan_id},
                )

                check_sources(conn)

                # Exécuter les huit étapes dans la même transaction.
                for job in JOBS:
                    run_job(conn, job, apply=True)

                updated = lire_pret(conn, loan_id)
                expected = initial[0] + 1

                if (
                    updated.montant_source != expected
                    or updated.montant_dw != expected
                ):
                    raise RuntimeError(
                        "La mise à jour du prêt a échoué."
                    )

                print("\nTEST MISE A JOUR REUSSI")

                # L'exception sort de engine.begin() et déclenche
                # l'annulation de toutes les écritures du test.
                raise ErreurSimulee("Erreur volontaire de fin de test")

        except ErreurSimulee:
            print("Erreur simulée interceptée. Transaction annulée.")

        # Vérifier les données après annulation.
        with write_engine.connect() as conn:
            with conn.begin():
                conn.execute(text("SET TRANSACTION READ ONLY"))
                verify_test_database(conn)
                restored = tuple(lire_pret(conn, loan_id))

                if restored != initial:
                    raise RuntimeError(
                        "ECHEC : les montants initiaux ne sont pas rétablis."
                    )

        print("TEST ROLLBACK REUSSI")
        print("Les montants source et DW ont retrouvé leurs valeurs initiales.")

    finally:
        write_engine.dispose()


if __name__ == "__main__":
    main()