import csv
import time
import logging
import requests
import pandas as pd
import os
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError, ArgumentError
from typing_extensions import Any

from src.config import BASE_URL, HEADER_JSON, DATA_DIR
from sqlalchemy import create_engine

load_dotenv()

logger = logging.getLogger(__name__)

def extract_sql():
    """Queries PostgreSQL for max_date for active sensors and their latest ingested timestamps."""

    engine = create_engine(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}")

    with engine.begin() as conn:
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

        df_sql = pd.read_sql(query, conn)

        logger.info("Dataframe is created and DB connection is closed")

        if df_sql.empty:
            logger.info("No measurements found in database. Incremental extraction cannot start.")
            return None
    return df_sql

def select_csv_file():
    """Finds the next available CSV path in DATA_DIR ( reuses empty latest file or increments index )."""
    files = list(DATA_DIR.glob("measurements_*.csv"))

    if files:
        latest_file = max(
            files,
            key=lambda file: int(file.stem.split("_")[-1])
        )

        try:
            df1 = pd.read_csv(latest_file)
            is_empty = df1.empty
        except pd.errors.EmptyDataError:
            is_empty = True

        file_stem = latest_file.stem.split("_")[-1]
        if is_empty:
            file_index = int(file_stem)
            logger.debug("Reusing the latest empty file again")
        else:
            file_index = int(file_stem) + 1

        file_name = DATA_DIR / f"measurements_{file_index}.csv"

    else:
        file_name = DATA_DIR / "measurements_1.csv"

    return file_name

def download_sensor(sensor_id: int, new_date: pd.Timestamp) -> dict[str, Any]:

    records = requests.get(f"{BASE_URL}/sensors/{sensor_id}/days?date_from={new_date}&limit=1000",
                           headers=HEADER_JSON, timeout=20)
    records.raise_for_status()
    records_json = records.json()

    # Wait 2 seconds between requests to avoid rapid request bursts and 429 errors
    time.sleep(2)

    return records_json


def sensor_transformation(records_json: dict[str, Any], sensor_id: int, location_id: int, location_name: str) -> list[dict]:
    measurement_list = []

    if 'results' in records_json and records_json['results'] != []:

        logger.debug("Received measurements for sensor %s", sensor_id)

        results = records_json['results']

        for record in results:
            if record['period']['datetimeFrom']['local'] is None:
                continue
            measurement_dict = {
                'location_id': location_id,
                'location_name': location_name,
                'sensor_id': sensor_id,
                'value': record['value'],
                'parameter_id': record['parameter']['id'],
                'parameter_name': record['parameter']['name'],
                'parameter_unit': record['parameter']['units'],
                'datetime': record['period']['datetimeFrom']['local']
            }
            measurement_list.append(measurement_dict)

    else:
        logger.debug("Ignoring empty sensors: %s from API", sensor_id)

    return measurement_list


def write_to_csv(input_df, file_name):
    """Orchestrates DB metadata lookup, API data fetching, transformation, and CSV export."""
    logger.info(">>> Incremental extraction Started <<<")

    fieldnames = ['location_id', 'location_name', 'sensor_id', 'value', 'parameter_id', 'parameter_name',
                  'parameter_unit', 'datetime']

    with open(file_name, mode='w', encoding='utf-8', newline='') as cf:
        logger.info("New file created - %s", file_name.name)
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()

        for row in input_df.itertuples(index=False):

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
                records_json = download_sensor(sensor_id, new_date)
            except requests.Timeout as e:
                logger.exception("Sensor %s timed out: %s", sensor_id, e)
                continue
            except requests.ConnectionError as e:
                logger.exception("Network connection failed for sensor %s: %s", sensor_id, e)
                continue
            except requests.exceptions.HTTPError as e:
                logger.error("HTTP error for sensor %s: %s", sensor_id, e)

                if e.response.status_code == 401:
                    logger.exception("Extraction failed due to unauthorized api key")
                    break
                elif e.response.status_code == 403:
                    logger.exception("Access forbidden")
                    break
                elif e.response.status_code == 429:
                    logger.exception("Rate limit hit. Stopping extraction. Next run will resume.")
                    break
                else:
                    logger.exception("Unhandled HTTP status %s for sensor %s, skipping", e.response.status_code,
                                   sensor_id)
                    continue

            except Exception as e:
                logger.exception("Unexpected error while processing sensor %s: %s", sensor_id, e)
                continue

            measurement_list = sensor_transformation(records_json, sensor_id, location_id, location_name)

            writer.writerows(measurement_list)

            logger.debug("Writing sensor: %s measurements to the csv file", sensor_id)


        logger.info("Incremental extraction completed")


def run_incremental_extract():
    try:
        df = extract_sql()
    except ArgumentError as e:
        logger.exception(f"Error: {e}")
        raise
    except SQLAlchemyError as e:
        logger.exception(f"Database connection failed: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error (e.g., missing driver): {e}")
        raise

    if df is None or df.empty:
        return None

    file_name = select_csv_file()

    return write_to_csv(df, file_name)