import csv
from unittest.mock import patch, Mock

import pandas as pd
import pytest
from requests.exceptions import Timeout,ConnectionError, HTTPError
from src.incremental.extract_incremental import run_incremental_extract, extract_sql, download_sensor, write_to_csv
from sqlalchemy.exc import ArgumentError, SQLAlchemyError


class TestOpenAQIncremental:
    @pytest.mark.parametrize('exception, expected_exception',[
            (ArgumentError("bad argument at construction time"), ArgumentError),
            (SQLAlchemyError("Connection Failed"), SQLAlchemyError)
        ])
    def test_extract_sql(self, exception, expected_exception):
        """
                Verify that database connection/engine errors raise expected exceptions
                and output appropriate error logs without proceeding to API extraction.
        """
        with patch('src.incremental.extract_incremental.create_engine') as sql_mock:

            sql_mock.side_effect = exception
            with pytest.raises(expected_exception):
                extract_sql()



    @pytest.mark.parametrize('raised_exception, expected_logs, expected_exception', [
        (ArgumentError("bad argument at construction time"), "Error: bad argument at construction time", ArgumentError),
        (SQLAlchemyError("Connection Failed"), "Database connection failed: Connection Failed", SQLAlchemyError)
    ])

    def test_extract_sql_in_run_incremental_extract(self,caplog,raised_exception, expected_logs, expected_exception):
        caplog.set_level('ERROR')

        with patch('src.incremental.extract_incremental.extract_sql', side_effect= raised_exception):

            with pytest.raises(expected_exception):
                run_incremental_extract()

            assert expected_logs in caplog.text

    @pytest.mark.parametrize('exception, expected_exception', [
        (Timeout("timed out"), Timeout),
        (ConnectionError("conn failed"), ConnectionError),
        (HTTPError("bad status"), HTTPError),
    ])
    def test_download_sensor_raises(self, exception, expected_exception):
        with patch('src.incremental.extract_incremental.requests.get', side_effect=exception):
            with pytest.raises(expected_exception):
                download_sensor(sensor_id=123, new_date=pd.Timestamp("2024-01-01"))



    @pytest.mark.parametrize('raised_exception, expected_logs',[
        (Timeout("API call timed out"), "Sensor 87357 timed out: API call timed out"),
        (ConnectionError("connection failed"), "Network connection failed for sensor 87357: connection failed")
    ])
    def test_download_sensor_raises_in_run_incremental_extract(self, caplog, tmp_path, raised_exception, expected_logs):
        caplog.set_level('ERROR')

        df = pd.DataFrame({
            'sensor_id': [87356, 87357, 87358],
            'max_date': [pd.Timestamp('2024-01-01')] * 3,
            'location_id': [101, 102, 103],
            'location_name': ['LocA', 'LocB', 'LocC'],
            'parameter_id': [201, 202, 203],
            'parameter_name': ['pm25', 'no2', 'no']
        })

        file_name = tmp_path/"output.csv"

        with patch('src.incremental.extract_incremental.download_sensor') as mock_download:
            mock_download.side_effect = [
                {"results": [{"value": 10, "parameter": {"id": 201, "name": "pm25", "units": "µg/m³"},
                              "period": {"datetimeFrom": {"local": "2024-01-01T00:00:00"}}}]},
                raised_exception,
                {"results": [{"value": 30, "parameter": {"id": 203, "name": "no", "units": "ppb"},
                              "period": {"datetimeFrom": {"local": "2024-01-02T00:00:00"}}}]}
            ]

            # with pytest.raises(expected_exception):
            write_to_csv(df,file_name)

            assert file_name.exists()

            with file_name.open('r', encoding='utf-8') as f:
                reader = list(csv.DictReader(f))

                assert reader[0] == {'location_id': '101', 'location_name': 'LocA', 'sensor_id': '87356',
                                     'value': '10', 'parameter_id': '201', 'parameter_name': 'pm25',
                                     'parameter_unit': 'µg/m³', 'datetime': '2024-01-01T00:00:00'}

                assert reader[1] == {'location_id': '103', 'location_name': 'LocC', 'sensor_id': '87358',
                                     'value': '30', 'parameter_id': '203', 'parameter_name': 'no',
                                     'parameter_unit': 'ppb', 'datetime': '2024-01-02T00:00:00'}

            assert expected_logs in caplog.text


    @pytest.mark.parametrize('raised_exception, expected_logs, status_code', [
        (HTTPError, "Extraction failed due to unauthorized api key", 401),
        (HTTPError, "Access forbidden", 403),
        (HTTPError, "Rate limit hit. Stopping extraction. Next run will resume.", 429)
    ])
    def test_download_sensor_raises_HTTP_in_run_incremental_extract(self, caplog, tmp_path, raised_exception, expected_logs, status_code):
        caplog.set_level('ERROR')

        df = pd.DataFrame({
            'sensor_id': [87356, 87357, 87358],
            'max_date': [pd.Timestamp('2024-01-01')] * 3,
            'location_id': [101, 102, 103],
            'location_name': ['LocA', 'LocB', 'LocC'],
            'parameter_id': [201, 202, 203],
            'parameter_name': ['pm25', 'no2', 'no']
        })

        file_name = tmp_path / "output.csv"

        with patch('src.incremental.extract_incremental.download_sensor') as mock_download:
            mock_response = Mock(status_code=status_code)  # fake object, has .status_code
            http_error = raised_exception(response=mock_response)  # real exception, .response = our fake object
            mock_download.side_effect = [
                {"results": [{"value": 10, "parameter": {"id": 201, "name": "pm25", "units": "µg/m³"},
                              "period": {"datetimeFrom": {"local": "2024-01-01T00:00:00"}}}]},
                http_error,
                {"results": [{"value": 30, "parameter": {"id": 203, "name": "no", "units": "ppb"},
                              "period": {"datetimeFrom": {"local": "2024-01-02T00:00:00"}}}]}
            ]

            # with pytest.raises(expected_exception):
            write_to_csv(df,file_name)

            assert file_name.exists()

            with file_name.open('r', encoding='utf-8') as f:
                reader = list(csv.DictReader(f))

                assert reader[0] == {'location_id': '101', 'location_name': 'LocA', 'sensor_id': '87356',
                                     'value': '10', 'parameter_id': '201', 'parameter_name': 'pm25',
                                     'parameter_unit': 'µg/m³', 'datetime': '2024-01-01T00:00:00'}

            assert mock_download.call_count == 2
            assert expected_logs in caplog.text  # when download_sensor() is CALLED, raise this