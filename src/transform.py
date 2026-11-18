import pandas as pd


def transform_districts(df):
    required_columns = {
        "district_id",
        "unemployment_95",
        "crimes_95",
    }

    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(
            f"Colonnes manquantes : {sorted(missing_columns)}"
        )

    result = df.copy(deep=True)

    if result["district_id"].isna().any():
        raise ValueError("Un district_id est manquant.")

    if result["district_id"].duplicated().any():
        raise ValueError("Des district_id sont en double.")

    for column in ("unemployment_95", "crimes_95"):
        values = pd.to_numeric(result[column], errors="raise")

        if values.isna().any():
            mean_value = values.mean()

            if pd.isna(mean_value):
                raise ValueError(
                    f"Impossible de compléter {column} : "
                    "aucune valeur connue."
                )

            values = values.fillna(mean_value)

        result[column] = values

    return result