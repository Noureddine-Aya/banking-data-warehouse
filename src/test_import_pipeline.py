"""Tester l'import et l'ETL dans une transaction toujours annulee."""

import argparse
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from dotenv import load_dotenv
import psycopg
from psycopg import sql
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import os

import import_staging
from etl_banking_test import JOBS, check_sources, run_job


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    args = parser.parse_args()
    folder = import_staging.find_folder(args.data_dir)
    counts = import_staging.inspect_files(folder)
    if not args.env_file.is_file():
        raise RuntimeError('Fichier .env introuvable')
    load_dotenv(args.env_file, override=True)
    url = URL.create(
        'postgresql+psycopg', username=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database='banking_dw_test',
    )
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            transaction = conn.begin()
            try:
                if conn.execute(text('SELECT current_database()')).scalar_one() != 'banking_dw_test':
                    raise RuntimeError('Base incorrecte')
                conn.execute(text("SET LOCAL lock_timeout = '10s'"))
                conn.execute(text("SET LOCAL statement_timeout = '180s'"))
                if not conn.execute(text('SELECT pg_try_advisory_xact_lock(7439218)')).scalar_one():
                    raise RuntimeError('Un autre chargement est en cours')

                raw = conn.connection.driver_connection
                tables = sql.SQL(', ').join(
                    sql.Identifier('staging', table)
                    for table, _ in import_staging.FILES.values()
                )
                with raw.cursor() as cur:
                    # Aucun CASCADE ni RESTART IDENTITY.
                    cur.execute(sql.SQL('TRUNCATE TABLE {}').format(tables))

                @contextmanager
                def existing_connection(**settings):
                    if settings.get('dbname') != 'banking_dw_test':
                        raise RuntimeError('Base incorrecte dans import_files')
                    # Reutiliser la transaction du test sans commit intermediaire.
                    yield raw

                with patch.object(import_staging.psycopg, 'connect', existing_connection):
                    import_staging.import_files(folder, counts, args.env_file)

                print('TEST IMPORT TSV REUSSI : huit tables chargees et comptees')
                check_sources(conn)
                for job in JOBS:
                    run_job(conn, job, apply=True)

                # Comparer chaque projection source a sa destination.
                for table, key, column_names, source in JOBS:
                    columns = column_names.split()
                    incoming = ', '.join(f's.{column}' for column in columns)
                    existing = ', '.join(f'd.{column}' for column in columns)
                    differences = conn.execute(text(f'''
                        WITH s AS ({source})
                        SELECT COUNT(*) FROM s LEFT JOIN dw.{table} d
                            ON d.{key} = s.{key}
                        WHERE d.{key} IS NULL OR
                            ROW({incoming}) IS DISTINCT FROM ROW({existing})
                    ''')).scalar_one()
                    if differences:
                        raise RuntimeError(f'{table} : {differences} lignes non conformes')
                print('TEST IMPORT + ETL REUSSI : huit projections sources conformes au DW')
            finally:
                transaction.rollback()
                print('ROLLBACK effectue : toutes les ecritures de ce test sont annulees.')
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
