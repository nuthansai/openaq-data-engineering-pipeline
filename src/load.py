import logging
import pandas as pd
from sqlalchemy import create_engine, URL
from sqlalchemy.dialects.postgresql import insert
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

        url = URL.create(
            drivername="postgresql",
            username=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            database=DB_NAME
        )

        engine = create_engine(url)

        with engine.begin() as conn:

            logger.info(">>> Connection established to PostgreSQL <<<")

            insert_location = insert(locations).values(location_record)
            do_nothing_loc = insert_location.on_conflict_do_nothing(index_elements = ["location_id"])

            loc_result = conn.execute(do_nothing_loc)
            loc_inserted_count = loc_result.rowcount

            insert_parameter = insert(parameters).values(parameter_record)
            do_nothing_par = insert_parameter.on_conflict_do_nothing(index_elements=["parameter_id"])

            par_result = conn.execute(do_nothing_par)
            par_inserted_count = par_result.rowcount


            insert_sensor = insert(sensors).values(sensor_record)
            do_nothing_sensor = insert_sensor.on_conflict_do_nothing(index_elements = ["sensor_id"])

            sensor_result = conn.execute(do_nothing_sensor)
            sensor_inserted_count = sensor_result.rowcount


            insert_measurement = insert(measurements).values(measurement_record)
            do_nothing_mes = insert_measurement.on_conflict_do_nothing(index_elements=['sensor_id', 'parameter_id', 'datetime'])

            mes_result = conn.execute(do_nothing_mes)
            mes_inserted_count = mes_result.rowcount


        loc_duplicates = len(location_record) - loc_inserted_count

        loc_stats = {
            'locations_attempted': len(location_record),
            'locations_inserted': loc_inserted_count,
            'location_duplicates': loc_duplicates
        }
        logger.info(f"Load summary: {loc_stats}")

        par_duplicates = len(parameter_record) - par_inserted_count

        par_stats = {
            'parameters_attempted': len(parameter_record),
            'parameters_inserted': par_inserted_count,
            'parameter_duplicates': par_duplicates
        }
        logger.info(f"Load summary: {par_stats}")

        sensor_duplicates = len(sensor_record) - sensor_inserted_count

        sensor_stats = {
            'sensors_attempted': len(sensor_record),
            'sensors_inserted': sensor_inserted_count,
            'sensor_duplicates': sensor_duplicates
        }
        logger.info(f"Load summary: {sensor_stats}")

        mes_duplicates = len(measurement_record) - mes_inserted_count

        mes_stats = {
            'measurement_attempted': len(measurement_record),
            'measurement_inserted': mes_inserted_count,
            'measurement_duplicates': mes_duplicates
        }
        logger.info(f"Load summary: {mes_stats}")

    except ArgumentError as e:

        logger.exception("invalid connection URL: %s", e)
        raise

    except SQLAlchemyError as e:

        logger.exception("Database connection failed: %s", e)
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