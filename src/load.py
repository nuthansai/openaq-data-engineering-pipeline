import logging

import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError, ArgumentError

from src.config import DATA_DIR

from src.sql_models import locations, parameters, sensors, measurements
load_dotenv()

logger = logging.getLogger(__name__)

def load_postgres():

    try:

        logger.info(">>> Incremental loading Started <<<")

        engine = create_engine(
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")



        files = DATA_DIR.glob("measurements_*.csv")
        latest_file = max(files, key= lambda file: int(file.stem.split('_')[-1]))
        df = pd.read_csv(latest_file)

        logger.debug("dataframe created from %s", latest_file.name)

        with engine.begin() as conn:

            logger.info(">>> Connection established to PostgreSQL <<<")

            df['datetime'] = pd.to_datetime(df['datetime'])

            location_df = df[['location_id', 'location_name']].drop_duplicates()
            # location_df.to_sql('locations', con=conn, if_exists='append', index=False)

            location_record = location_df.to_dict(orient="records")
            insert_location = insert(locations).values(location_record)
            do_nothing_loc = insert_location.on_conflict_do_nothing(index_elements = ["location_id"])
            conn.execute(do_nothing_loc)

            parameter_df = df[['parameter_id', 'parameter_name', 'parameter_unit']].drop_duplicates()
            # parameter_df.to_sql('parameters', con=conn, if_exists='append', index=False)

            parameter_record = parameter_df.to_dict(orient="records")
            insert_parameter = insert(parameters).values(parameter_record)
            do_nothing_par = insert_parameter.on_conflict_do_nothing(index_elements=["parameter_id"])
            conn.execute(do_nothing_par)

            sensor_df = df[['sensor_id', 'location_id']].drop_duplicates()
            # sensor_df.to_sql('sensors', con=conn, if_exists='append', index=False)

            sensor_record = sensor_df.to_dict(orient="records")
            insert_sensor = insert(sensors).values(sensor_record)
            do_nothing_sensor = insert_sensor.on_conflict_do_nothing(index_elements = ["sensor_id"])
            conn.execute(do_nothing_sensor)

            measurement_df = df[['sensor_id', 'parameter_id', 'datetime', 'value']]
            # measurement_df.to_sql('measurements', con=conn, if_exists='append', index=False)

            measurement_record = measurement_df.to_dict(orient="records")
            insert_measurement = insert(measurements).values(measurement_record)
            do_nothing_mes = insert_measurement.on_conflict_do_nothing(index_elements=['sensor_id', 'parameter_id', 'datetime'])
            conn.execute(do_nothing_mes)



    except ArgumentError as e:

        logger.exception("invalid connection URL: %s", e)
        raise

    except SQLAlchemyError as e:

        logger.exception("Database connection failed: %s", e)
        raise

    except pd.errors.EmptyDataError as e:
        logger.error('Empty File: %s', e)
        raise
    except Exception as e:

        logger.exception("Unexpected error (e.g., missing driver): %s", e)
        raise





    logger.info(">>> Incremental loading completed successfully <<<")
