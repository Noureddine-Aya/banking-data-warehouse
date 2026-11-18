"""Verifier les TSV, puis les importer explicitement dans une base de test vide."""

import argparse
import csv
import os
from pathlib import Path

from dotenv import load_dotenv
import psycopg
from psycopg import sql


# L'ordre correspond aux fichiers TSV, pas a l'ordre physique des tables.
FILES = {
    'fin_district.tsv': ('district', (
        'district_id district_name region inhabitants municipalities_1 '
        'municipalities_2 municipalities_3 municipalities_4 cities urban_ratio '
        'salary unemployment_95 unemployment_96 entrepreneurs crimes_95 crimes_96'
    ).split()),
    'fin_account.tsv': ('account', 'account_id district_id date frequency'.split()),
    'fin_client.tsv': ('client', 'client_id birth_date gender district_id'.split()),
    'fin_disp.tsv': ('disp', 'disp_id client_id account_id type'.split()),
    'fin_card.tsv': ('card', 'card_id disp_id type issued'.split()),
    'fin_loan.tsv': ('loan', 'loan_id account_id date amount duration payments status'.split()),
    'fin_order.tsv': ('payment_order', 'order_id account_id bank_to account_to amount k_symbol'.split()),
    'fin_trans.tsv': ('trans', 'trans_id account_id date amount balance type operation k_symbol bank account'.split()),
}


def find_folder(path):
    candidates = [path] + [p for p in path.iterdir() if p.is_dir()]
    matches = [p for p in candidates if all((p / name).is_file() for name in FILES)]
    if len(matches) != 1:
        raise ValueError('Indiquer le dossier contenant les huit fichiers fin_*.tsv.')
    return matches[0]


def read_rows(path, columns):
    with path.open('r', encoding='utf-8-sig', newline='') as stream:
        for number, row in enumerate(csv.reader(stream, delimiter='\t', quoting=csv.QUOTE_NONE), 1):
            if len(row) != len(columns):
                raise ValueError(
                    f'{path.name}, ligne {number} : {len(row)} colonnes '
                    f'au lieu de {len(columns)}'
                )
            # Les champs vides, espaces seuls et ? representent des absences.
            # Les identifiants de comptes destinataires restent des textes.
            yield [None if value.strip() in ('', '?') else value for value in row]


def inspect_files(folder):
    counts = {}
    for filename, (_, columns) in FILES.items():
        count = 0
        missing = 0
        for row in read_rows(folder / filename, columns):
            count += 1
            missing += sum(value is None for value in row)
        if count == 0:
            raise ValueError(f'{filename} est vide.')
        counts[filename] = count
        print(f'{filename} : {count} lignes, {len(columns)} colonnes, '
              f'{missing} champs manquants')
    return counts


def import_files(folder, counts, env_file):
    if not env_file.is_file():
        raise ValueError('Fichier de configuration .env introuvable.')
    load_dotenv(env_file, override=True)
    settings = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'user': os.environ['DB_USER'],
        'password': os.environ['DB_PASSWORD'],
        'dbname': 'banking_dw_test',
        'connect_timeout': 10,
    }
    with psycopg.connect(**settings) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT current_database()')
            if cur.fetchone()[0] != 'banking_dw_test':
                raise RuntimeError('Base incorrecte.')
            cur.execute("SET LOCAL lock_timeout = '10s'")
            cur.execute("SET LOCAL statement_timeout = '180s'")

            # Verifier toutes les tables avant la premiere insertion.
            tables = sql.SQL(', ').join(
                sql.Identifier('staging', table) for table, _ in FILES.values()
            )
            cur.execute(sql.SQL('LOCK TABLE {} IN EXCLUSIVE MODE').format(tables))
            for table, _ in FILES.values():
                cur.execute(sql.SQL('SELECT EXISTS (SELECT 1 FROM {})').format(
                    sql.Identifier('staging', table)
                ))
                if cur.fetchone()[0]:
                    raise RuntimeError(
                        f'staging.{table} contient deja des donnees. Import refuse.'
                    )

            for filename, (table, columns) in FILES.items():
                statement = sql.SQL('COPY {} ({}) FROM STDIN').format(
                    sql.Identifier('staging', table),
                    sql.SQL(', ').join(map(sql.Identifier, columns)),
                )
                with cur.copy(statement) as copy:
                    for row in read_rows(folder / filename, columns):
                        copy.write_row(row)
                cur.execute(sql.SQL('SELECT COUNT(*) FROM {}').format(
                    sql.Identifier('staging', table)
                ))
                count = cur.fetchone()[0]
                if count != counts[filename]:
                    raise RuntimeError(f'Comptage incorrect pour {table}.')
                print(f'staging.{table} : {count} lignes importees')
    print('Import valide dans banking_dw_test.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, default=Path('.env'))
    parser.add_argument('--apply-test', action='store_true')
    args = parser.parse_args()
    folder = find_folder(args.data_dir)
    print(f'Dossier : {folder}')
    counts = inspect_files(folder)
    if args.apply_test:
        import_files(folder, counts, args.env_file)
    else:
        print('Verification des fichiers terminee. Aucune connexion a PostgreSQL.')


if __name__ == '__main__':
    main()
