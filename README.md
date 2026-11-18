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

## Origine des données

Ce projet utilise la version adaptée pour Teradata du jeu de données bancaire tchèque du PKDD’99 Discovery Challenge, préparé initialement par Petr Berka et Marta Sochorova.

Les fichiers utilisés sont disponibles dans le [dépôt source de dnoeth](https://github.com/dnoeth/1999_Czech_financial_dataset_Teradata).

Selon la documentation de cette version, les dates ont été décalées de 20 ans, les montants ont été divisés par 10 et les descriptions tchèques ont été remplacées par des abréviations anglaises. Les montants ne constituent donc pas une conversion officielle en euros ou en dollars.

Les huit fichiers sources sont au format TSV. Ils doivent être téléchargés séparément pour préparer les tables `staging`.

## Vérification et import des fichiers TSV

Télécharger et extraire les données depuis le dépôt source indiqué
dans la section « Origine des données ».

### Vérifier les fichiers

Depuis la racine du projet, remplacer le chemin ci-dessous par
celui du dossier contenant les fichiers téléchargés.

```powershell
python src/import_staging.py --data-dir "C:\chemin\vers\donnees"
```

Cette commande vérifie le nombre de colonnes et compte les lignes
et les champs manquants, sans connexion à PostgreSQL.

### Importer dans la base de test

Prérequis : créer `banking_dw_test`, y exécuter `sql/schema.sql`
et renseigner les identifiants PostgreSQL dans `.env`.

Les huit tables `staging` doivent être vides.

```powershell
python src/import_staging.py --data-dir "C:\chemin\vers\donnees" --env-file .env --apply-test
```

L’import utilise une seule transaction. Il refuse les tables staging
déjà remplies et annule les insertions si une erreur survient.

Les champs vides, composés uniquement d’espaces ou contenant `?`
sont convertis en NULL.

La vérification des fichiers a été exécutée avec succès.
Le mode d’import en base reste à tester.