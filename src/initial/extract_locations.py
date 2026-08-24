import json
import requests

from src.config import HEADER_JSON, BASE_URL,DATA_DIR

try:
    r_country = requests.get(f"{BASE_URL}/locations?countries_id=9",headers=HEADER_JSON)

    with open(DATA_DIR / "India_locations.json",
              mode="w", encoding="utf-8") as f:
        json.dump(r_country.json(), f)
except requests.ConnectionError as e:
    print(f"Network failed :{e}")
except Exception as e:
    print(e)




# -------------------------------------------------------------------
# Exploration Code (Version 1)
#
# Purpose:
# Retrieve measurements for the first 5 locations and all available
# sensors. This was an initial exploration to understand the
# Measurements API.
#
# Limitations:
# - Downloads data for every sensor.
# - Not scalable.
# - No location selection criteria.
# - Superseded by the structured extraction pipeline below.
# -------------------------------------------------------------------

# with open(DATA_DIR/"india_locations.json", mode="r", encoding="utf-8") as f:
#     json_data = json.load(f)
#
# results = json_data['results']
# measurements_dict= {}
#
#
# measurements_id_dict = {}
#
# for result in results[:5]:
#     measurements_list = []
#     measurements_id_list = []
#
#
#     for sensor in result['sensors']:
#         sensor_ids = sensor['id']
#         r_measurements = requests.get(f"https://api.openaq.org/v3/sensors/{sensor_ids}/measurements", headers=header_json)
#         response_json = r_measurements.json()
#         if 'results' in response_json and response_json['results'] != []:
#             measurements_id_list.append(sensor['id'])
#             measurements_list.extend(response_json['results'])
#         else:
#             continue
#     measurements_dict[result['name']] = measurements_list
#     measurements_id_dict[result['name']] = measurements_id_list
#
# with open(DATA_DIR/'location_measurement_data.json', mode='w', encoding='utf-8') as f:
#     json.dump(measurements_dict,f)
#
# with open(DATA_DIR/'location_measurement_id.json', mode='w', encoding='utf-8') as f:
#     json.dump(measurements_id_dict, f)



# ---------------------------------------------------------------------------
# Read all extracted India locations and create a metadata file containing
# only the locations that are currently active (latest measurements available
# in 2026). For each selected location, store the location ID, location name,
# first and last measurement timestamps.
# ---------------------------------------------------------------------------

with open(DATA_DIR/'India_locations.json', mode='r',encoding='utf-8') as f:
    results = json.load(f)

response_json = results['results']



location_measurements_id_list = []

sensor_count = 0

for result in response_json:

    if result['datetimeFirst'] is not None and result['datetimeLast']['local'].startswith('2026') and result['datetimeFirst']['local'].startswith('2025'):
        measurements_dict = {}

        measurements_dict['location_id'] = result['id']
        measurements_dict['location_name'] = result['name']

        measurements_dict['datetimeFirst'] = result['datetimeFirst']
        measurements_dict['datetimeLast'] = result['datetimeLast']

        sensor_id_list = []

        for sensor in result['sensors']:
            sensor_id_list.append(sensor['id'])

        measurements_dict['sensor_id'] = sensor_id_list


        location_measurements_id_list.append(measurements_dict)
        print(f"len(sensor_id_list): {len(sensor_id_list)}")
        sensor_count += len(sensor_id_list)
with open(DATA_DIR/'selected_locations.json', mode='w', encoding='utf-8') as f:
    json.dump(location_measurements_id_list, f)

print(sensor_count)

# Read selected locations and identify stations that started reporting in
# 2025 and are still active in 2026. Used to identify recent monitoring
# stations for the project.

# with open(DATA_DIR/'selected_locations.json', mode='r', encoding='utf-8') as f:
#     results = json.load(f)
#
# latest_locations_list = []
#
# for result in results:
#     if (
#         result['datetimeFirst']['local'].startswith('2025')
#         and result['datetimeLast']['local'].startswith('2026')
#     ):
#         latest_locations_list.append(result['location_name'])
#
# print(latest_locations_list)

# Create a small sample dataset consisting of five representative locations.
# Used for developing and testing the measurement extraction pipeline.

# with open(DATA_DIR/'selected_locations.json', mode='r', encoding='utf-8') as f:
#     results = json.load(f)
#
# sample_locations = []
#
# for result in results:
#     if result['location_name'] in [
#         'Kasturi Nagar, Bengaluru - KSPCB',
#         'HB Colony, Vijayawada - APPCB',
#         'Rabindra Bharati University, Kolkata - WBPCB',
#         'Bandra Kurla Complex, Mumbai - IITM',
#         'Pusa, Delhi - DPCC'
#     ]:
#         sample_locations.append(result)
#
# with open(DATA_DIR/'sample_locations.json', mode='w', encoding='utf-8') as f:
#     json.dump(sample_locations, f)