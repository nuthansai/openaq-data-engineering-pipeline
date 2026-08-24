import csv
import json

import ijson
import pandas as pd
from src.config import PROJECT_ROOT,DATA_DIR

with open(DATA_DIR/'measurements_data.json', mode='rb') as f, open(DATA_DIR/'measurements.csv','w',newline = '', encoding='utf-8') as cf:
    data = ijson.items(f,'item')

# print(data[0]['sensor'][0]['measurements'][0]) # 1 measurement of a sensor of 1 location

# print(data[0])


    writer = None

    for location in data:
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

                if writer is None:
                    writer = csv.DictWriter(
                        cf,
                        fieldnames=measurement_dict.keys()
                    )
                    writer.writeheader()

                writer.writerow(measurement_dict)

# df = pd.DataFrame(measurements_list)

# print(measurements_list)
#
# print(df.drop_duplicates())

