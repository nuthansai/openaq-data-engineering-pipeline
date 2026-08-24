import csv
import time
import logging
import requests
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError, ArgumentError
from src.config import BASE_URL, HEADER_JSON, DATA_DIR, LOG_DIR
from sqlalchemy import create_engine

load_dotenv()

logger = logging.getLogger(__name__)


def incremental_extract():

    try:
        logger.info(">>> Incremental extraction Started <<<")

        engine = create_engine(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")

        with engine.connect() as conn:
            pass

        logger.info(">>> Connection established to PostgreSQL <<<")

        query = '''
                SELECT
                    l.location_id,
                    l.location_name,
                    m.sensor_id,
                    p.parameter_id,
                    p.parameter_name,
                    MAX(m.datetime) AS max_date
                FROM measurements m
                JOIN sensors s USING(sensor_id)
                JOIN locations l USING(location_id)
                JOIN parameters p USING(parameter_id)
                GROUP BY l.location_id,m.sensor_id,p.parameter_id,p.parameter_name
                ORDER BY location_id;
            '''

        df_sql = pd.read_sql(query, engine)

        if df_sql.empty:
            logger.info("No measurements found in database. Incremental extraction cannot start.")
            return

        logger.info("Dataframe is created and DB connection is closed")

    except ArgumentError:
        logger.exception("Error: ")
        raise
    except SQLAlchemyError:
        logger.exception("Database connection failed: ")
        raise
    except Exception as e:
        logger.exception("Unexpected error (e.g., missing driver): ")
        raise




    files = DATA_DIR.glob("measurements_*.csv")

    latest_file = max(
        files,
        key=lambda file: int(file.stem.split("_")[-1])
    )

    try:
        df1 = pd.read_csv(latest_file)
        is_empty = df1.empty
    except pd.errors.EmptyDataError:
        is_empty = True



    if is_empty:
        file_index = int(latest_file.stem.split("_")[-1])
        logger.debug("Reusing the latest empty file again")
    else:
        file_index = int(latest_file.stem.split("_")[-1]) + 1

    file_name = DATA_DIR / f"measurements_{file_index}.csv"


    fieldnames = ['location_id', 'location_name', 'sensor_id', 'value', 'parameter_id', 'parameter_name', 'parameter_unit', 'datetime']



    with open(file_name, mode='w', encoding='utf-8', newline='') as cf:
        logger.info("New file created - %s", file_name.name)
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()

        for i, row in enumerate(df_sql.itertuples(index=False),start=1):
            sensor_id = row.sensor_id
            date = row.max_date
            location_id = row.location_id
            location_name = row.location_name
            new_date = date + pd.Timedelta(days=1)

            logger.debug(
                "Processing sensor %s | date=%s | location_id=%s | location=%s | new_date=%s",
                sensor_id, date, location_id, location_name, new_date
            )
            try:
                records = requests.get(f"{BASE_URL}/sensors/{sensor_id}/days?date_from={new_date}&limit=1000",headers=HEADER_JSON, timeout=20)
                records.raise_for_status()
                records_json = records.json()

                reset = int(records.headers.get("x-ratelimit-reset"))

                if 'results' in records_json and records_json['results'] != []:

                    logger.debug("Received measurements for sensor %s", sensor_id)

                    results = records_json['results']
                    measurement_list = []
                    for record in results:
                        if record['period']['datetimeFrom']['local'] is None:
                            continue
                        measurement_dict = {
                            'location_id'     : location_id,
                            'location_name'   : location_name,
                            'sensor_id'       : sensor_id,
                            'value'           : record['value'],
                            'parameter_id'    : record['parameter']['id'],
                            'parameter_name'  : record['parameter']['name'],
                            'parameter_unit'  : record['parameter']['units'],
                            'datetime'        : record['period']['datetimeFrom']['local']
                        }
                        measurement_list.append(measurement_dict)

                    # row_count += len(measurement_list)

                    writer.writerows(measurement_list)

                    logger.debug("Writing sensor: %s measurements to the csv file", sensor_id)

                    # if row_count >= chunk_size:
                    #     file_index += 1


                else:
                    logger.debug("Ignoring empty sensors: %s from API", sensor_id)
                    continue

                # Wait 2 seconds between requests to avoid rapid request bursts and 429 errors
                time.sleep(2)

            except requests.Timeout:
                logger.warning("Sensor %s timed out", sensor_id)
                continue
            except requests.ConnectionError as e:
                logger.warning("Network connection failed for sensor %s: %s", sensor_id, e)
                continue
            except requests.exceptions.HTTPError as e:
                logger.error("HTTP error for sensor %s: %s", sensor_id, e)

                if records.status_code == 401:
                    break
            except Exception:
                logger.exception("Unexpected error while processing sensor %s", sensor_id)
                raise

    logger.info("Incremental extraction completed")