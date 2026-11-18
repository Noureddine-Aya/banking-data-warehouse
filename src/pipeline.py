from compare_dw import compare_dimensions
import logging
from datetime import datetime

from audit_etl import main as run_audit
from extract import extract_districts
from transform import transform_districts
from load import preview_load


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("BankingETL")


def run_pipeline():
    start = datetime.now()
    logger.info("Démarrage du pipeline en lecture seule")

    try:
        logger.info("ETAPE 1 : Audit préalable")
        run_audit()

        logger.info("ETAPE 2 : Extraction des districts")
        raw_df = extract_districts()

        logger.info("ETAPE 3 : Transformation")
        clean_df = transform_districts(raw_df)

        logger.info("ETAPE 4 : Aperçu des districts")
        preview_load(clean_df)

        logger.info("ETAPE 5 : Comparaison des comptes et clients")
        compare_dimensions()

        logger.info("Pipeline terminé sans erreur")

    except Exception:
        logger.exception("Echec du pipeline")
        raise

    finally:
        logger.info("Durée totale : %s", datetime.now() - start)


if __name__ == "__main__":
    run_pipeline()