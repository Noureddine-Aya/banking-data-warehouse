
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import text

from db_writer import write_engine
from extract import extract_districts
from transform import transform_districts


def load_districts(clean_df, dry_run=True):
    """Charger uniquement les valeurs manquantes existantes."""

    if clean_df["district_id"].isna().any():
        raise ValueError("Identifiants de district manquants")

    if clean_df["district_id"].duplicated().any():
        raise ValueError("Doublons de districts détectés")

    print("\nETL - CHARGEMENT DES DISTRICTS")
    print("-" * 45)

    updates = []

    # Transaction : annulée automatiquement si erreur.
    with write_engine.begin() as conn:

        for row in clean_df.itertuples(index=False):
            district_id = int(row.district_id)

            value = Decimal(
                str(row.unemployment_95)
            ).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )

            existing = conn.execute(
                text("""
                    SELECT unemployment_95
                    FROM dw.dim_district
                    WHERE district_id = :id
                    FOR UPDATE
                """),
                {"id": district_id}
            ).first()

            if existing is None:
                raise ValueError(
                    f"District {district_id} introuvable"
                )

            if existing[0] is None:
                updates.append((district_id, value))

        print(f"Districts analysés : {len(clean_df)}")
        print(f"Mises à jour nécessaires : {len(updates)}")

        for district_id, value in updates:
            print(f"District {district_id} : NULL -> {value}")

        if dry_run:
            print("\nMODE SIMULATION")
            print("Aucune modification effectuée.")
            return

        # Ecriture autorisée uniquement en mode APPLY.
        for district_id, value in updates:
            conn.execute(
                text("""
                    UPDATE dw.dim_district
                    SET unemployment_95 = :value
                    WHERE district_id = :id
                      AND unemployment_95 IS NULL
                """),
                {"id": district_id, "value": value}
            )

        print(f"\nMises à jour appliquées : {len(updates)}")


if __name__ == "__main__":
    raw_df = extract_districts()
    clean_df = transform_districts(raw_df)

    # Sécurité : simulation par défaut
    load_districts(clean_df, dry_run=True)
