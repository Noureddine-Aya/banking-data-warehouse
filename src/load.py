
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
from sqlalchemy import text

from extract import engine, extract_districts
from transform import transform_districts


def preview_load(clean_df: pd.DataFrame):
    """Comparer les districts nettoyés au Data Warehouse."""

    # Lecture des colonnes existantes dans le DW
    query = text("""
        SELECT
            d.district_id,
            d.unemployment_95,
            s.unemployment_95 AS valeur_source
        FROM dw.dim_district d
        LEFT JOIN staging.district s
            ON s.district_id = d.district_id
        ORDER BY d.district_id
    """)

    with engine.connect() as connection:
        existing_df = pd.read_sql_query(query, connection)

    # Respecter la précision NUMERIC(6,2) de PostgreSQL
    clean_df = clean_df.copy()

    clean_df["unemployment_95"] = clean_df["unemployment_95"].apply(
        lambda value: float(
            Decimal(str(value)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP
            )
        )
    )

    # Comparaison sans modifier les données
    comparison = clean_df[
        ["district_id", "unemployment_95"]
    ].merge(
        existing_df,
        on="district_id",
        how="left",
        suffixes=("_new", "_existing"),
        indicator=True
    )

    # Conserver la valeur existante si la source est manquante.
    preserve_existing = (
        comparison["_merge"].eq("both")
        & comparison["valeur_source"].isna()
        & comparison["unemployment_95_existing"].notna()
    )

    comparison.loc[
        preserve_existing, "unemployment_95_new"
    ] = comparison.loc[
        preserve_existing, "unemployment_95_existing"
    ]

    print(
        "\nValeurs DW conservées car la source est manquante : "
        f"{int(preserve_existing.sum())}"
    )

    new_rows = comparison[
        comparison["_merge"] == "left_only"
    ]

    changed_rows = comparison[
        (comparison["_merge"] == "both")
        &
        (
            comparison["unemployment_95_new"].ne(
                comparison["unemployment_95_existing"]
            )
        )
    ]

    print("\nPREVISUALISATION DU CHARGEMENT")
    print("-" * 45)
    print(f"Districts extraits : {len(clean_df)}")
    print(f"Districts existants : {len(existing_df)}")
    print(f"Nouveaux districts : {len(new_rows)}")
    print(f"Districts avec différences : {len(changed_rows)}")

    if not changed_rows.empty:
        print("\nDifférences détectées :")
        print(changed_rows.to_string(index=False))

    print("\nAucune donnée PostgreSQL n'a été modifiée.")


if __name__ == "__main__":
    raw_df = extract_districts()
    clean_df = transform_districts(raw_df)
    preview_load(clean_df)
