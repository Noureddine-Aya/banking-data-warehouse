# Data Warehouse bancaire et ETL Python

Projet personnel de Data Engineering utilisant Python et PostgreSQL
pour intégrer et analyser plus d’un million de transactions bancaires.

Le projet couvre l’import de fichiers TSV, le chargement d’un Data
Warehouse, les contrôles de qualité et les analyses SQL.

## Technologies

- Python 3.12
- PostgreSQL 18
- SQLAlchemy et psycopg
- pandas
- pytest
- Git et GitHub

## Architecture

```text
Fichiers TSV
    |
    v
Schéma staging — 8 tables sources
    |
    v
Contrôles et transformations ETL
    |
    v
Schéma dw — 5 dimensions et 3 tables de faits
    |
    v
Analyses SQL
```

### Tables sources

| Fichier | Table staging | Nombre de lignes |
|---|---|---:|
| fin_account.tsv | account | 4 500 |
| fin_client.tsv | client | 5 369 |
| fin_disp.tsv | disp | 5 369 |
| fin_card.tsv | card | 892 |
| fin_district.tsv | district | 77 |
| fin_loan.tsv | loan | 682 |
| fin_order.tsv | payment_order | 6 471 |
| fin_trans.tsv | trans | 1 056 320 |

### Data Warehouse

Les cinq dimensions sont :

- `dw.dim_district`
- `dw.dim_account`
- `dw.dim_client`
- `dw.dim_date`
- `dw.dim_operation`

Les trois tables de faits sont :

- `dw.fact_loans`
- `dw.fact_payment_orders`
- `dw.fact_transactions`

Les données de cartes et de dispositions sont conservées dans
`staging`. Elles n’ont pas de table cible dédiée dans ce modèle.

## Fonctionnalités

- Vérification de la structure des fichiers TSV.
- Import transactionnel des huit fichiers sources.
- Simulation ETL en lecture seule par défaut.
- Chargement des dimensions avant les faits.
- Recherche des clés des dimensions pour alimenter les faits.
- Insertion des nouvelles lignes et mise à jour des lignes différentes.
- Conservation des clés techniques existantes.
- Réexécution sans modification des lignes identiques.
- Contrôles des références source et des dates obligatoires des faits.
- Annulation de la transaction en cas d’erreur.
- Analyses des transactions mensuelles et des prêts par statut.

## Origine des données

Le projet utilise la version adaptée pour Teradata du jeu de données
bancaire tchèque du PKDD’99 Discovery Challenge, préparé initialement
par Petr Berka et Marta Sochorova.

Les fichiers sont disponibles dans le
[dépôt source de dnoeth](https://github.com/dnoeth/1999_Czech_financial_dataset_Teradata).

Selon la documentation de cette version :

- Les dates ont été décalées de 20 ans.
- Les montants ont été divisés par 10.
- Les descriptions tchèques ont été remplacées par des abréviations
  anglaises.

Les montants ne constituent pas une conversion officielle en euros
ou en dollars.

Télécharger et extraire les huit fichiers `fin_*.tsv` depuis le dépôt
source. Ces fichiers sont séparés par des tabulations et ne comportent
pas de ligne d’en-tête.

## Règles de traitement

### Import TSV

Les champs vides, composés uniquement d’espaces ou contenant `?`
sont convertis en `NULL`.

L’ordre des colonnes est défini explicitement pour chaque fichier.
Les numéros de comptes destinataires sont conservés comme textes.

### Opérations

Les opérations absentes ou vides sont rattachées au code `UNKNOWN`.

Les clés techniques et les libellés existants sont réutilisés.
Un libellé générique est créé pour les nouveaux codes.

### Districts

Pour `unemployment_95`, une valeur existante dans le DW est conservée
si la source est manquante.

Lors d’une première insertion, une valeur source manquante reste
à `NULL`.

Le module historique `transform.py` propose également un nettoyage
par moyenne, testé séparément. Le chargeur complet
`etl_banking_test.py` applique la règle de conservation décrite ici.

### Dates

La dimension date est alimentée à partir des dates nécessaires
aux prêts et aux transactions.

- Clé au format `AAAAMMJJ`.
- Numérotation des jours de lundi = 1 à dimanche = 7.
- Samedi et dimanche identifiés comme jours de week-end.

## Organisation du dépôt

```text
banking-data-engineering/
├── sql/
│   ├── schema.sql
│   └── analyses_olap.sql
├── src/
│   ├── import_staging.py
│   ├── etl_banking_test.py
│   ├── audit_etl.py
│   ├── compare_dw.py
│   ├── test_etl_transaction.py
│   ├── test_import_pipeline.py
│   └── autres modules et scripts de développement
├── tests/
│   ├── test_transform.py
│   └── test_load_safe.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

`import_staging.py` et `etl_banking_test.py` sont les points d’entrée
pour reproduire le pipeline complet.

Les anciens modules d’extraction, de transformation et de chargement
documentent les étapes de développement du projet.

## Installation

### Prérequis

- Python 3.12.
- PostgreSQL 18 démarré.
- Accès à un serveur PostgreSQL avec les droits nécessaires.
- Les huit fichiers TSV téléchargés et extraits.

### Préparer Python

Depuis la racine du dépôt, dans PowerShell :

```powershell
python -m venv .venv
```

```powershell
.\.venv\Scripts\Activate.ps1
```

```powershell
python -m pip install -r requirements.txt
```

### Configurer la connexion

Créer le fichier local `.env` à partir du modèle :

```powershell
Copy-Item .env.example .env
```

Renseigner les paramètres du serveur PostgreSQL :

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_USER=your_postgresql_user
DB_PASSWORD=your_postgresql_password
DB_NAME=banking_dw
```

Les scripts d’import et de chargement complet ciblent explicitement
`banking_dw_test`, indépendamment de `DB_NAME`.

Les modules historiques d’audit et de comparaison utilisent
`banking_dw`. Ils nécessitent donc cette base lorsqu’ils sont
exécutés séparément.

Le fichier `.env` est exclu du dépôt par `.gitignore`.

## Préparation de la base de test

Les instructions suivantes concernent une nouvelle installation.

Créer une base vide nommée `banking_dw_test` dans pgAdmin.

Le fichier `sql/schema.sql` définit les huit tables sources et
les huit tables du DW, leurs clés, leurs séquences et leurs contraintes.

Depuis la racine du projet, exécuter la commande suivante.
Adapter le chemin des outils PostgreSQL et l’utilisateur si nécessaire.

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h localhost -p 5432 -U postgres -d banking_dw_test -v ON_ERROR_STOP=1 --single-transaction -f sql/schema.sql
```

Cette commande crée les structures dans la base vide.
Elle doit être exécutée une seule fois pour cette installation.

## Vérification des fichiers TSV

Remplacer le chemin d’exemple par celui du dossier des données :

```powershell
python src/import_staging.py --data-dir "C:\chemin\vers\donnees"
```

Le script recherche les huit fichiers dans le dossier indiqué
ou dans un de ses sous-dossiers directs.

Il vérifie le nombre de colonnes et affiche les nombres de lignes
et de champs manquants. Ce mode fonctionne sans connexion à PostgreSQL.

## Import dans staging

Les huit tables `staging` doivent être vides.

```powershell
python src/import_staging.py --data-dir "C:\chemin\vers\donnees" --env-file .env --apply-test
```

Le script :

- Vérifie la base cible.
- Refuse les tables sources déjà remplies.
- Importe les huit fichiers dans une seule transaction.
- Vérifie les nombres de lignes importées.
- Annule les insertions si une erreur survient.

## Simulation ETL

```powershell
python src/etl_banking_test.py --env-file .env
```

La simulation affiche les nouvelles lignes et les lignes différentes
sans écrire dans la base.

Si les dimensions sont encore vides, les références des faits sont
signalées comme restant à résoudre. Elles seront recherchées après
le chargement des dimensions lors de l’exécution réelle.

## Chargement ETL dans la base de test

Cette commande écrit dans `banking_dw_test` :

```powershell
python src/etl_banking_test.py --env-file .env --apply-test
```

Le chargeur exécute les huit étapes dans une seule transaction.

Une seconde exécution sur les mêmes données doit afficher zéro
insertion et zéro mise à jour pour les huit tables.

## Tests

### Nettoyage des districts

```powershell
python -m pytest tests/test_transform.py -v
```

Les trois tests vérifient :

- Le remplacement des valeurs manquantes par la moyenne dans le
  module historique de nettoyage.
- Le refus des identifiants de district en double.
- La conservation des données source en mémoire.

### Mise à jour et rollback

Après avoir chargé les sources et le DW :

```powershell
python src/test_etl_transaction.py
```

Le test modifie temporairement le montant d’un prêt, exécute
les huit étapes ETL, vérifie la mise à jour du fait correspondant,
puis provoque une erreur pour annuler la transaction.

Il vérifie ensuite le rétablissement des montants source et DW
du prêt choisi.

### Import TSV suivi du traitement ETL

Exécuter ce test sur la base de test préparée et chargée, en dehors
des autres traitements ETL :

```powershell
python src/test_import_pipeline.py --data-dir "C:\chemin\vers\donnees" --env-file .env
```

Le test :

1. Vide temporairement les huit tables `staging` dans une transaction.
2. Importe les fichiers TSV avec le code de l’importeur.
3. Exécute les huit étapes ETL.
4. Vérifie que chaque ligne source projetée correspond au DW.
5. Annule toutes les écritures de la transaction.

Ce test verrouille temporairement les tables sources.

## Résultats vérifiés

Les exécutions réalisées sur la base de test ont permis de vérifier :

- Le chargement des cinq dimensions et des trois tables de faits.
- L’intégration de 1 056 320 transactions.
- Une seconde exécution avec zéro insertion et zéro mise à jour.
- La mise à jour d’un prêt et son annulation après erreur simulée.
- L’import des huit fichiers TSV et leur traitement ETL dans
  une transaction annulée à la fin.

Lors du test d’import, la normalisation des champs manquants a
entraîné temporairement 1 379 mises à jour d’ordres de paiement
et 553 304 mises à jour de transactions.

Ces nombres concordent avec les comptages des `k_symbol` vides
ou contenant un marqueur d’absence dans les anciennes données.

## Analyses SQL

Le fichier `sql/analyses_olap.sql` contient deux analyses :

- Nombre de transactions et somme des montants par mois.
- Nombre de prêts, montants et durées moyennes par code de statut.

La somme des montants des transactions représente leur volume.
Elle ne correspond pas à un bénéfice ni à un flux net.

## État du projet

Version portfolio finalisée pour le périmètre Data Warehouse,
ETL Python et analyses SQL.

Le projet a été exécuté et vérifié dans un environnement PostgreSQL
local de test. Les scripts de chargement complet ciblent
`banking_dw_test`.