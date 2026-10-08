import logging
import pandas as pd
from PIL.ImageChops import duplicate
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine.url import URL
from sqlalchemy.exc import SQLAlchemyError, ArgumentError
from src.config import DATA_DIR, DB_USER, DB_PASSWORD, DB_HOST, DB_NAME
from src.sql_models import locations, parameters, sensors, measurements


logger = logging.getLogger(__name__)

def read_from_csv(file):

    try:

        df = pd.read_csv(file)

        logger.debug("dataframe created from %s", file.name)

    except pd.errors.EmptyDataError as e:
        logger.error('Empty File %s: %s', file.name, e)
        raise

    return df

def load_postgres(location_record, parameter_record, sensor_record, measurement_record):

    try:
        logger.info(">>> Incremental loading Started <<<")

        db_url = URL.create(
            drivername="postgresql",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            database=DB_NAME
        )

        engine = create_engine(db_url)

        with engine.begin() as conn:

            logger.info(">>> Connection established to PostgreSQL <<<")

            insert_location = insert(locations).values(location_record)
            do_nothing_loc = insert_location.on_conflict_do_nothing(index_elements = ["location_id"])

            result_loc = conn.execute(do_nothing_loc)
            location_rows_affected = result_loc.rowcount
            location_duplicate_count = len(location_record) - location_rows_affected

            location_stats = {
                'locations_attempted': len(location_record),
                'locations_inserted': location_rows_affected,
                'location_duplicates': location_duplicate_count
            }
            logger.info(f"Load summary: {location_stats}")


            insert_parameter = insert(parameters).values(parameter_record)
            do_nothing_par = insert_parameter.on_conflict_do_nothing(index_elements=["parameter_id"])

            result_par = conn.execute(do_nothing_par)
            parameter_rows_affected = result_par.rowcount
            parameter_duplicate_count = len(parameter_record) - parameter_rows_affected

            parameter_stats = {
                'locations_attempted': len(parameter_record),
                'locations_inserted': parameter_rows_affected,
                'parameter_duplicates': parameter_duplicate_count
            }
            logger.info(f"Load summary: {parameter_stats}")


            insert_sensor = insert(sensors).values(sensor_record)
            do_nothing_sensor = insert_sensor.on_conflict_do_nothing(index_elements = ["sensor_id"])
            result_sensor = conn.execute(do_nothing_sensor)

            sensor_rows_affected = result_sensor.rowcount
            sensor_duplicate_count = len(location_record) - sensor_rows_affected

            sensor_stats = {
                'locations_attempted': len(location_record),
                'locations_inserted': sensor_rows_affected,
                'measurements_duplicates': sensor_duplicate_count
            }
            logger.info(f"Load summary: {sensor_stats}")


            insert_measurement = insert(measurements).values(measurement_record)
            do_nothing_mes = insert_measurement.on_conflict_do_nothing(index_elements=['sensor_id', 'parameter_id', 'datetime'])


            result_mes = conn.execute(do_nothing_mes)
            mes_rows_affected = result_mes.rowcount
            mes_duplicate_count = len(location_record) - mes_rows_affected

            mes_stats = {
                'locations_attempted': len(location_record),
                'locations_inserted': mes_rows_affected,
                'measurements_duplicates': mes_duplicate_count
            }
            logger.info(f"Load summary: {mes_stats}")

    except ArgumentError as e:

        logger.exception("invalid connection URL: %s", e)
        raise

    except SQLAlchemyError as e:

        logger.exception("Database error during load: %s", e)
        raise


    except Exception as e:

        logger.exception("Unexpected error (e.g., missing driver): %s", e)
        raise

    logger.info(">>> Incremental loading completed successfully <<<")


def load_orchestrator():

    files = DATA_DIR.glob("measurements_*.csv")
    latest_file = max(files, key=lambda file: int(file.stem.split('_')[-1]))

    csv_df = read_from_csv(latest_file)

    if csv_df.empty:
        logger.info("No data found in csv. Incremental loading cannot start.")
        return None

    csv_df['datetime'] = pd.to_datetime(csv_df['datetime'])

    location_df = csv_df[['location_id', 'location_name']].drop_duplicates()
    location_record = location_df.to_dict(orient="records")

    parameter_df = csv_df[['parameter_id', 'parameter_name', 'parameter_unit']].drop_duplicates()
    parameter_record = parameter_df.to_dict(orient="records")

    sensor_df = csv_df[['sensor_id', 'location_id']].drop_duplicates()
    sensor_record = sensor_df.to_dict(orient="records")

    measurement_df = csv_df[['sensor_id', 'parameter_id', 'datetime', 'value']]
    measurement_record = measurement_df.to_dict(orient="records")

    load_postgres(location_record, parameter_record, sensor_record, measurement_record)

    return None