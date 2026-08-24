import requests
import json
from src.config import HEADER_JSON, BASE_URL, DATA_DIR

with open(DATA_DIR / 'selected_locations.json', mode='r', encoding='utf-8') as f:
    results = json.load(f)

measurements_data_list = []

for result in results:

    sensor_ids = result['sensor_id']

    measurement_data_dict = {
        'location_id': result['location_id'],
        'location_name': result['location_name']
    }

    sensor_measurements_list = []

    for sensor_id in sensor_ids:

        try:
            r_measurements = requests.get(
                f"{BASE_URL}/sensors/{sensor_id}/days?limit=375",
                headers=HEADER_JSON,
                timeout=5
            )

            r_measurements.raise_for_status()
            response_json = r_measurements.json()

            if 'results' in response_json and response_json['results'] != []:

                sensor_measurements_dict = {
                    'sensor_id': sensor_id,
                    'measurements': response_json['results']
                }

                sensor_measurements_list.append(sensor_measurements_dict)
                measurement_data_dict['sensor'] = sensor_measurements_list

            else:
                continue

        except requests.Timeout as e:
            print(f"Request timed out for sensor {sensor_id}: {e}")
            continue

        except requests.ConnectionError as e:
            print(f"Network failed for sensor {sensor_id}: {e}")
            continue

        except requests.HTTPError as e:
            print(f"HTTP error for sensor {sensor_id}: {e}")

            if r_measurements.status_code == 401:
                print("Invalid credentials. Stopping extraction.")
                raise

            if r_measurements.status_code == 403:
                print("Access forbidden. Stopping extraction.")
                raise

            if r_measurements.status_code == 429:
                print("Rate limit exceeded. Stopping extraction.")
                raise

            continue

        except Exception as e:
            print(f"Unexpected error for sensor {sensor_id}: {e}")
            continue

    if sensor_measurements_list:
        measurement_data_dict['sensor'] = sensor_measurements_list

    measurements_data_list.append(measurement_data_dict)


with open(
    DATA_DIR / 'measurements_data.json',
    mode='w',
    encoding='utf-8'
) as f:
    json.dump(measurements_data_list, f)