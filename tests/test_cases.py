import pytest
from src.initial.extract_locations import extract_location
from src.initial.transform_measurements import transform

data_1 = [{
      "id": 12, "name": "SPARTAN - IIT Kanpur", "locality": None,
      "timezone": "Asia/Kolkata",
      "country": {"id": 9, "code": "IN", "name": "India"},
      "sensors": [
        {
          "id": 23,
          "name": "pm25 \u00b5g/m\u00b3",
          "parameter": {
            "id": 2,
            "name": "pm25",
            "units": "\u00b5g/m\u00b3",
            "displayName": "PM2.5"
          }
        }
      ],
      "distance": None,
      "datetimeFirst": None,
      "datetimeLast": None
    },
    {
      "id": 13, "name": "Delhi Technological University, Delhi - CPCB", "locality": None,
      "timezone": "Asia/Kolkata",
      "country": {"id": 9, "code": "IN", "name": "India"},
      "sensors": [
        {
          "id": 13866,
          "name": "no2 \u00b5g/m\u00b3",
          "parameter": {
            "id": 5,
            "name": "no2",
            "units": "\u00b5g/m\u00b3",
            "displayName": "NO\u2082 mass"
          }
        },
        {
          "id": 24,
          "name": "o3 \u00b5g/m\u00b3",
          "parameter": {
            "id": 3,
            "name": "o3",
            "units": "\u00b5g/m\u00b3",
            "displayName": "O\u2083 mass"
          }
        },
        {
          "id": 13864,
          "name": "pm25 \u00b5g/m\u00b3",
          "parameter": {
            "id": 2,
            "name": "pm25",
            "units": "\u00b5g/m\u00b3",
            "displayName": "PM2.5"
          }
        }
      ],
      "distance": None,
      "datetimeFirst": {
        "utc": "2016-11-02T19:00:00Z",
        "local": "2016-11-03T00:30:00+05:30"
      },
      "datetimeLast": {
        "utc": "2018-02-22T04:00:00Z",
        "local": "2018-02-22T09:30:00+05:30"
      }
    },
    {
        "id": 5408, "name": "Secretariat, Amaravati - APPCB", "locality": None, "timezone": "Asia/Kolkata",
        "country": {"id": 9, "code": "IN", "name": "India"},
        "sensors": [
            {
                "id": 12234943,
                "name": "co ppb",
                "parameter": {
                    "id": 102,
                    "name": "co",
                    "units": "ppb",
                    "displayName": "CO"
                }
            },
            {
                "id": 12234944,
                "name": "no ppb",
                "parameter": {
                    "id": 24,
                    "name": "no",
                    "units": "ppb",
                    "displayName": "NO"
                }
            },
            {
                "id": 12234945,
                "name": "no2 ppb",
                "parameter": {
                    "id": 15,
                    "name": "no2",
                    "units": "ppb",
                    "displayName": "NO\u2082"
                }
            },
            {
                "id": 14340731,
                "name": "nox ppb",
                "parameter": {
                    "id": 23,
                    "name": "nox",
                    "units": "ppb",
                    "displayName": "NOX"
                }
            },
            {
                "id": 12234946,
                "name": "o3 \u00b5g/m\u00b3",
                "parameter": {
                    "id": 3,
                    "name": "o3",
                    "units": "\u00b5g/m\u00b3",
                    "displayName": "O\u2083 mass"
                }
            },
            {
                "id": 12234947,
                "name": "pm10 \u00b5g/m\u00b3",
                "parameter": {
                    "id": 1,
                    "name": "pm10",
                    "units": "\u00b5g/m\u00b3",
                    "displayName": "PM10"
                }
            },
            {
                "id": 12234948,
                "name": "pm25 \u00b5g/m\u00b3",
                "parameter": {
                    "id": 2,
                    "name": "pm25",
                    "units": "\u00b5g/m\u00b3",
                    "displayName": "PM2.5"
                }
            },
            {
                "id": 12234949,
                "name": "relativehumidity %",
                "parameter": {
                    "id": 98,
                    "name": "relativehumidity",
                    "units": "%",
                    "displayName": "RH"
                }
            },
            {
                "id": 12234950,
                "name": "so2 ppb",
                "parameter": {
                    "id": 101,
                    "name": "so2",
                    "units": "ppb",
                    "displayName": "SO\u2082"
                }
            },
            {
                "id": 12234951,
                "name": "temperature c",
                "parameter": {
                    "id": 100,
                    "name": "temperature",
                    "units": "c",
                    "displayName": "Temperature (C)"
                }
            },
            {
                "id": 14340732,
                "name": "wind_direction deg",
                "parameter": {
                    "id": 22,
                    "name": "wind_direction",
                    "units": "deg",
                    "displayName": "Wind direction"
                }
            },
            {
                "id": 14340733,
                "name": "wind_speed m/s",
                "parameter": {
                    "id": 34,
                    "name": "wind_speed",
                    "units": "m/s",
                    "displayName": "Wind speed"
                }
            }
        ],
        "datetimeFirst": {
            "utc": "2025-02-18T20:15:00Z",
            "local": "2025-02-19T01:45:00+05:30"
        },
        "datetimeLast": {
            "utc": "2026-06-15T06:00:00Z",
            "local": "2026-06-15T11:30:00+05:30"
        }
    }
]

expected_1 = [{'location_id': 5408,
                       'location_name': "Secretariat, Amaravati - APPCB",
                       'datetimeFirst': {"utc": "2025-02-18T20:15:00Z", "local": "2025-02-19T01:45:00+05:30"},
                       "datetimeLast": {"utc": "2026-06-15T06:00:00Z", "local": "2026-06-15T11:30:00+05:30"},
                       'sensor_id':[12234943, 12234944, 12234945, 14340731, 12234946, 12234947, 12234948, 12234949, 12234950, 12234951, 14340732, 14340733]
                    }]

data_2 = [
        {
            "id": 12, "name": "SPARTAN - IIT Kanpur", "locality": None,
            "timezone": "Asia/Kolkata",
            "country": {"id": 9, "code": "IN", "name": "India"},
            "sensors": [
                {
                    "id": 23,
                    "name": "pm25 \u00b5g/m\u00b3",
                    "parameter": {
                        "id": 2,
                        "name": "pm25",
                        "units": "\u00b5g/m\u00b3",
                        "displayName": "PM2.5"
                    }
                }
            ],
            "distance": None,
            "datetimeFirst": None,
            "datetimeLast": None
        }
    ]

expected_2 = []

data_3 = [
        {
            "id": 13, "name": "Delhi Technological University, Delhi - CPCB", "locality": None,
            "timezone": "Asia/Kolkata",
            "country": {"id": 9, "code": "IN", "name": "India"},
            "sensors": [
                {
                    "id": 13866,
                    "name": "no2 \u00b5g/m\u00b3",
                    "parameter": {
                        "id": 5,
                        "name": "no2",
                        "units": "\u00b5g/m\u00b3",
                        "displayName": "NO\u2082 mass"
                    }
                },
                {
                    "id": 24,
                    "name": "o3 \u00b5g/m\u00b3",
                    "parameter": {
                        "id": 3,
                        "name": "o3",
                        "units": "\u00b5g/m\u00b3",
                        "displayName": "O\u2083 mass"
                    }
                },
                {
                    "id": 13864,
                    "name": "pm25 \u00b5g/m\u00b3",
                    "parameter": {
                        "id": 2,
                        "name": "pm25",
                        "units": "\u00b5g/m\u00b3",
                        "displayName": "PM2.5"
                    }
                }
            ],
            "distance": None,
            "datetimeFirst": {
                "utc": "2016-11-02T19:00:00Z",
                "local": "2016-11-03T00:30:00+05:30"
            },
            "datetimeLast": {
                "utc": "2018-02-22T04:00:00Z",
                "local": "2018-02-22T09:30:00+05:30"
            }
        }
    ]

expected_3 = []

def test_transform():
    test_data = [
        {
            "location_id": 101,
            "location_name": "Hyderabad Central",
            "sensor": [
                {
                    "sensor_id": 1001,
                    "measurements": [
                        {
                            "value": 25.4,
                            "parameter": {
                                "id": 2,
                                "name": "pm25",
                                "units": "µg/m³"
                            },
                            "period": {
                                "datetimeFrom": {
                                    "local": "2026-09-01T10:00:00+05:30"
                                }
                            }
                        }
                    ]
                }
            ]
        }
    ]

    result = transform(test_data)

    actual = next(result)

    expected = {
        "location_id": 101,
        "location_name": "Hyderabad Central",
        "sensor_id": 1001,
        "value": 25.4,
        "parameter_id": 2,
        "parameter_name": "pm25",
        "parameter_unit": "µg/m³",
        "datetime": "2026-09-01T10:00:00+05:30"
    }

    assert actual == expected


@pytest.mark.parametrize("input_value, expected_value",[
    pytest.param(data_1, expected_1, id="extract_location_skips_entries_without_sensor_activity"),
    pytest.param(data_2, expected_2, id="extract_location_returns_empty_for_location_without_datetime"),
    pytest.param(data_3, expected_3, id="extract_location_returns_empty_for_location_with_old_record")
])
def test_extract_location_filters_by_activity_criteria(input_value, expected_value):
    result = extract_location(input_value)
    assert expected_value == result
