import json
import os

import requests
from dotenv import load_dotenv
from requests import ConnectTimeout

load_dotenv()

from src.config import HEADER_JSON, BASE_URL,DATA_DIR

# params = {
#     'limit':10
# }
#
# r = requests.get(f"{config.BASE_URL}/locations",params=params, headers=HEADER_JSON)
# r1 = requests.get(f"{config.BASE_URL}/instruments/5", headers=HEADER_JSON)
# r_location= requests.get(f"{config.BASE_URL}/locations/12",headers=HEADER_JSON)
# r_measurements= requests.get(f"{config.BASE_URL}/sensors/12235882/measurements",headers=HEADER_JSON)
# print(r_location.url)
# print(r_location.status_code)
# print(r_location.json())

# r_country = requests.get(f"{BASE_URL}/locations?limit=9",headers=HEADER_JSON)

# with open(f'{DATA_DIR}/India_locations.json', mode='w', encoding='utf-8') as f:
#     json.dump(r_country.json(), f)

# print(r_country.url)
# print(r_country.json())
try:
    r_measurements = requests.get(f"{BASE_URL}/sensors/1/days?limit=2", headers=HEADER_JSON)


    print(r_measurements.json())

    print(r_measurements.headers.get("x-ratelimit-used"))
    print(r_measurements.headers.get("x-ratelimit-limit"))
    print(r_measurements.headers.get("x-ratelimit-remaining"))
    print(type(r_measurements.headers.get("x-ratelimit-reset")))

except requests.exceptions.HTTPError as e:
    print(e)
except ConnectTimeout as e:
    print(e.args)
