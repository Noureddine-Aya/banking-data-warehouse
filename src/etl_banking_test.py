"""Simulation par defaut. Chargement explicite reserve a banking_dw_test."""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Les noms SQL ci-dessous sont fixes, jamais fournis par l'utilisateur.
DATE_SOURCE = """
SELECT date AS full_date FROM staging.loan WHERE date IS NOT NULL
UNION SELECT date FROM staging.trans WHERE date IS NOT NULL
"""

JOBS = [
    ('dim_district', 'district_id',
     'district_id district_name region inhabitants urban_ratio average_salary unemployment_95 unemployment_96 entrepreneurs',
     '''SELECT s.district_id, s.district_name, s.region, s.inhabitants,
        s.urban_ratio, s.salary AS average_salary,
        COALESCE(s.unemployment_95, d.unemployment_95) AS unemployment_95,
        s.unemployment_96, s.entrepreneurs
        FROM staging.district s LEFT JOIN dw.dim_district d USING (district_id)'''),
    ('dim_account', 'account_id',
     'account_id district_id opening_date statement_frequency',
     '''SELECT account_id, district_id, date AS opening_date,
        frequency AS statement_frequency FROM staging.account'''),
    ('dim_client', 'client_id', 'client_id birth_date gender district_id',
     'SELECT client_id, birth_date, gender, district_id FROM staging.client'),
    ('dim_date', 'full_date',
     'full_date date_key year quarter month day day_of_week is_weekend',
     f'''SELECT full_date, TO_CHAR(full_date, 'YYYYMMDD')::integer AS date_key,
        EXTRACT(YEAR FROM full_date)::integer AS year,
        EXTRACT(QUARTER FROM full_date)::integer AS quarter,
        EXTRACT(MONTH FROM full_date)::integer AS month,
        EXTRACT(DAY FROM full_date)::integer AS day,
        EXTRACT(ISODOW FROM full_date)::integer AS day_of_week,
        EXTRACT(ISODOW FROM full_date) IN (6,7) AS is_weekend
        FROM ({DATE_SOURCE}) dates'''),
    ('dim_operation', 'operation_code',
     'operation_code operation_label is_unknown',
     '''SELECT s.operation_code,
        COALESCE(NULLIF(BTRIM(d.operation_label), ''),
            CASE WHEN s.operation_code = 'UNKNOWN'
                 THEN 'Operation non renseignee'
                 ELSE 'Code operation : ' || s.operation_code END) AS operation_label,
        s.operation_code = 'UNKNOWN' AS is_unknown
        FROM (
            SELECT DISTINCT COALESCE(NULLIF(BTRIM(operation), ''), 'UNKNOWN')
                AS operation_code FROM staging.trans
            UNION SELECT 'UNKNOWN'
        ) s LEFT JOIN dw.dim_operation d USING (operation_code)'''),
    ('fact_loans', 'loan_id',
     'loan_id account_key date_key loan_amount duration_months monthly_payment loan_status',
     '''SELECT s.loan_id, a.account_key, d.date_key,
        s.amount AS loan_amount, s.duration AS duration_months,
        s.payments AS monthly_payment, s.status AS loan_status
        FROM staging.loan s
        LEFT JOIN dw.dim_account a USING (account_id)
        LEFT JOIN dw.dim_date d ON d.full_date = s.date'''),
    ('fact_payment_orders', 'order_id',
     'order_id account_key bank_to account_to amount k_symbol',
     '''SELECT s.order_id, a.account_key, s.bank_to, s.account_to, s.amount, s.k_symbol
        FROM staging.payment_order s
        LEFT JOIN dw.dim_account a USING (account_id)'''),
    ('fact_transactions', 'transaction_id',
     'transaction_id account_key date_key operation_key transaction_type amount balance k_symbol',
     '''SELECT s.trans_id AS transaction_id, a.account_key, d.date_key,
        o.operation_key, s.type AS transaction_type, s.amount, s.balance, s.k_symbol
        FROM staging.trans s
        LEFT JOIN dw.dim_account a USING (account_id)
        LEFT JOIN dw.dim_date d ON d.full_date = s.date
        LEFT JOIN dw.dim_operation o ON o.operation_code =
            COALESCE(NULLIF(BTRIM(s.operation), ''), 'UNKNOWN')'''),
]


def check_sources(conn):
    for table in ('loan', 'payment_order', 'trans'):
        count = conn.execute(text(f'''
            SELECT COUNT(*) FROM staging.{table} s
            WHERE NOT EXISTS (
                SELECT 1 FROM staging.account a WHERE a.account_id = s.account_id
            )''')).scalar_one()
        if count:
            raise RuntimeError(f'{table} : {count} comptes source manquants')
    for table in ('loan', 'trans'):
        count = conn.execute(text(
            f'SELECT COUNT(*) FROM staging.{table} WHERE date IS NULL'
        )).scalar_one()
        if count:
            raise RuntimeError(f'{table} : {count} dates manquantes')
    for table in ('account', 'client'):
        count = conn.execute(text(f'''
            SELECT COUNT(*) FROM staging.{table} s
            WHERE s.district_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM staging.district d WHERE d.district_id = s.district_id
            )''')).scalar_one()
        if count:
            raise RuntimeError(f'{table} : {count} districts source manquants')


def run_job(conn, job, apply):
    table, key, column_names, source = job
    columns = column_names.split()
    attributes = [column for column in columns if column != key]
    incoming = ', '.join(f's.{column}' for column in attributes)
    existing = ', '.join(f'd.{column}' for column in attributes)
    stats = conn.execute(text(f'''
        WITH s AS ({source})
        SELECT COUNT(*) AS total,
            COUNT(*) FILTER (WHERE d.{key} IS NULL) AS nouvelles,
            COUNT(*) FILTER (WHERE d.{key} IS NOT NULL AND
                ROW({incoming}) IS DISTINCT FROM ROW({existing})) AS differentes
        FROM s LEFT JOIN dw.{table} d ON d.{key} = s.{key}
    ''')).mappings().one()
    print(f"{table} : {stats['total']} sources, {stats['nouvelles']} nouvelles, "
          f"{stats['differentes']} differentes")

    required_keys = [c for c in columns if c.endswith('_key')]
    if table.startswith('fact_'):
        missing = conn.execute(text(f'''
            SELECT COUNT(*) FROM ({source}) s WHERE
            {' OR '.join(f's.{c} IS NULL' for c in required_keys)}
        ''')).scalar_one()
        if missing:
            print(f'  References dimensionnelles a resoudre : {missing} lignes')
            if apply:
                raise RuntimeError('References manquantes apres chargement des dimensions')

    if not apply:
        return

    # Filtrer avant INSERT evite les mises a jour inutiles et la consommation
    # des identites pour les lignes inchangees lors des reexecutions.
    assignments = ', '.join(f'{c} = EXCLUDED.{c}' for c in attributes)
    changed = ', '.join(f'EXCLUDED.{c}' for c in attributes)
    current = ', '.join(f'target.{c}' for c in attributes)
    result = conn.execute(text(f'''
        WITH s AS ({source})
        INSERT INTO dw.{table} AS target ({', '.join(columns)})
        SELECT {', '.join(f's.{c}' for c in columns)}
        FROM s LEFT JOIN dw.{table} d ON d.{key} = s.{key}
        WHERE d.{key} IS NULL OR
            ROW({incoming}) IS DISTINCT FROM ROW({existing})
        ON CONFLICT ({key}) DO UPDATE SET {assignments}
        WHERE ROW({current}) IS DISTINCT FROM ROW({changed})
    '''))
    print(f'  Lignes inserees ou mises a jour : {result.rowcount}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--apply-test', action='store_true')
    args = parser.parse_args()
    load_dotenv(args.env_file, override=True)
    url = URL.create('postgresql+psycopg', username=os.environ['DB_USER'],
                     password=os.environ['DB_PASSWORD'],
                     host=os.getenv('DB_HOST', 'localhost'),
                     port=int(os.getenv('DB_PORT', '5432')),
                     database='banking_dw_test')
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            mode = 'READ WRITE' if args.apply_test else 'READ ONLY'
            conn.execute(text(f'SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, {mode}'))
            conn.execute(text("SET LOCAL statement_timeout = '180s'"))
            conn.execute(text("SET LOCAL lock_timeout = '10s'"))
            database = conn.execute(text('SELECT current_database()')).scalar_one()
            if database != 'banking_dw_test':
                raise RuntimeError('Base de test incorrecte')
            if args.apply_test:
                locked = conn.execute(text(
                    'SELECT pg_try_advisory_xact_lock(7439218)'
                )).scalar_one()
                if not locked:
                    raise RuntimeError('Un chargement ETL est deja en cours')
            print(f"Base : {database} | Mode : {'CHARGEMENT TEST' if args.apply_test else 'SIMULATION'}")
            check_sources(conn)
            missing = conn.execute(text('''SELECT COUNT(*) FROM staging.district
                WHERE unemployment_95 IS NULL''')).scalar_one()
            print(f'Sources district sans unemployment_95 : {missing}')
            for job in JOBS:
                run_job(conn, job, args.apply_test)
        print('Transaction validee.' if args.apply_test else 'Simulation terminee en lecture seule.')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
