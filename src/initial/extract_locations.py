import json
from typing import List

import requests

from src.config import HEADER_JSON, BASE_URL,DATA_DIR

def initial_extraction():

    try:
        r_country = requests.get(f"{BASE_URL}/locations?countries_id=9",headers=HEADER_JSON, timeout=10)
        r_country.raise_for_status()
        with open(DATA_DIR / "India_locations.json",
                  mode="w", encoding="utf-8") as f:
            json.dump(r_country.json(), f)
    except requests.Timeout as e:
        print(f"Timed out: {e}")
        raise
    except requests.ConnectionError as e:
        print(f"Network failed :{e}")
        raise
    except requests.exceptions.HTTPError as e:
        if r_country.status_code == 401:
            print("failed due to unauthorized api key")
            raise
        elif r_country.status_code == 403:
            print("Access forbidden. Stopping extraction.")
            raise
        elif r_country.status_code == 429:
            print("API rate limit reached")
            raise
    except Exception as e:
        print(e)
        raise


# ---------------------------------------------------------------------------
# Read all extracted India locations and create a metadata file containing
# only the locations that are currently active (latest measurements available
# in 2026). For each selected location, store the location ID, location name,
# first and last measurement timestamps.
# ---------------------------------------------------------------------------


def extract_location(input_json: List[dict]) -> List[dict]:
    # sensor_count = 0
    location_measurements_id_list= []

    for result in input_json:

        # assumes datetimeFirst/datetimeLast are never asymmetric — verified against 2026 India dataset pull, not guaranteed long-term
        if result['datetimeFirst'] is not None and result['datetimeLast']['local'].startswith('2026') and result['datetimeFirst']['local'].startswith('2025'):
            measurements_dict = {
                'location_id': result['id'],
                'location_name' : result['name'],
                'datetimeFirst' : result['datetimeFirst'],
                'datetimeLast' : result['datetimeLast']
            }

            sensor_id_list = []

            for sensor in result['sensors']:
                sensor_id_list.append(sensor['id'])

            measurements_dict['sensor_id'] = sensor_id_list

            location_measurements_id_list.append(measurements_dict)

    return location_measurements_id_list


if __name__ == "__main__":
    initial_extraction()

    with open(DATA_DIR / 'India_locations.json', mode='r', encoding='utf-8') as f:
        results = json.load(f)

    response_json = results['results']

    result_list = extract_location(response_json)

    with open(DATA_DIR / 'selected_locations.json', mode='w', encoding='utf-8') as f:
        json.dump(result_list, f)