import csv
from typing import Any, Generator, Iterable

import ijson
from src.config import DATA_DIR


def transform(input_data: Iterable[dict]) -> Generator[dict[str, Any], Any, None]:
    for location in input_data:
        for sensor in location["sensor"]:
            for measurement in sensor["measurements"]:

                measurement_dict = {
                    "location_id": location["location_id"],
                    "location_name": location["location_name"],
                    "sensor_id": sensor["sensor_id"],
                    "value": measurement["value"],
                    "parameter_id": measurement["parameter"]["id"],
                    "parameter_name": measurement["parameter"]["name"],
                    "parameter_unit": measurement["parameter"]["units"],
                    "datetime": measurement["period"]["datetimeFrom"]["local"]
                }

                yield measurement_dict


with open(DATA_DIR / 'measurements_data.json', mode='rb') as f, \
        open(DATA_DIR / 'measurements5.csv', 'w', newline='', encoding='utf-8') as cf:
    data = ijson.items(f, 'item')
    result = transform(data)
    writer = None

    for result_dict in result:
        if writer is None:
            writer = csv.DictWriter(cf, fieldnames=result_dict.keys())
            writer.writeheader()
        writer.writerow(result_dict)
# df = pd.DataFrame(measurements_list)

# print(measurements_list)
#
# print(df.drop_duplicates())

