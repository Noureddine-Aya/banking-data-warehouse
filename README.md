# Data Warehouse bancaire et ETL Python

Projet personnel de traitement de données bancaires avec Python
et PostgreSQL, portant sur plus d’un million de transactions.

## Technologies

Python, PostgreSQL, SQLAlchemy, psycopg, pandas et pytest.

## Modèle de données

Le schéma `staging` contient les données sources.

Le schéma `dw` comprend cinq dimensions et trois tables de faits.

- Dimensions : district, compte, client, date et opération.
- Faits : prêts, ordres de paiement et transactions.

## Fonctionnalités

- Contrôles de qualité et comparaison des données source avec le DW.
- Simulation en lecture seule par défaut.
- Chargement des dimensions avant les faits.
- Insertions et mises à jour des lignes différentes.
- Réexécution sans doublons, vérifiée sur la base de test.
- Mise à jour d’un prêt et rollback après erreur simulée, vérifiés.

Les opérations vides sont rattachées au code `UNKNOWN`.
Pour `unemployment_95`, une valeur existante du DW est conservée
si la source est manquante. Lors d’une première insertion,
une valeur source manquante reste à NULL.

## Installation

Prérequis : Python 3.12 et PostgreSQL 18.

Depuis la racine du projet, dans PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Renseigner les paramètres PostgreSQL dans le fichier `.env`.

## Préparation des bases

Le script ETL utilise la base `banking_dw_test`.
Elle doit contenir les tables sources alimentées dans `staging`
et les tables cibles avec leurs contraintes dans `dw`.

Les scripts de création et les instructions d’import des sources
restent à ajouter pour permettre une installation complète.

## Simulation

```powershell
python src/etl_banking_test.py --env-file .env
```

## Chargement dans la base de test

Cette commande écrit dans `banking_dw_test`.

```powershell
python src/etl_banking_test.py --env-file .env --apply-test
```

## Test transactionnel

Ce test modifie temporairement un prêt, exécute les huit étapes ETL,
puis provoque une erreur pour vérifier l’annulation de la transaction.

```powershell
python src/test_etl_transaction.py
```

## État du projet

Le chargement et les contrôles ont été exécutés sur la base de test.

La documentation de préparation des données, les analyses OLAP
et le dashboard Power BI restent à compléter.

## Structure SQL
Le fichier `sql/schema.sql` contient la structure des 16 tables du projet.