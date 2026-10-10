import csv
from unittest.mock import patch

import pandas as pd
from pandas.errors import EmptyDataError
from sqlalchemy.exc import ArgumentError, SQLAlchemyError

from src.load import read_from_csv, load_postgres, load_orchestrator
import pytest


class TestOpenAQTest():


    def test_read_sql(self, tmp_path, caplog):
        caplog.set_level('ERROR')

        input_file = tmp_path/ "sensor_data.csv"
        input_file.write_text("")

        with patch('src.load.pd.read_csv') as mock_read_csv:
            mock_read_csv.side_effect = EmptyDataError("No columns to parse from file")
            with pytest.raises(EmptyDataError):
                read_from_csv(input_file)

        assert "Empty File sensor_data.csv: No columns to parse from file" in caplog.text

    @pytest.mark.parametrize('exception, expected_exception, expected_logs', [
        (ArgumentError("bad argument at construction time"), ArgumentError, "invalid connection URL: bad argument at construction time"),
        (SQLAlchemyError("Connection Failed"), SQLAlchemyError, "Database connection failed: Connection Failed")
    ])
    def test_load_postgres(self, caplog, exception, expected_exception, expected_logs):
        """
                Verify that database connection/engine errors raise expected exceptions
                and output appropriate error logs.
        """
        caplog.set_level('WARNING')

        location_record = [{'location_id': 101, 'location_name': 'locA'}, {'location_id': 102, 'location_name': 'locB'}]
        parameter_record = [{'parameter_id':201, 'parameter_name': 'no', 'parameter_unit': 'ppb'}, {'parameter_id':202, 'parameter_name': 'no2', 'parameter_unit': 'ppb'}]
        sensor_record = [{'sensor_id':301, 'location_id':101}, {'sensor_id':302, 'location_id':102}]
        measurement_record = [{'sensor_id':301, 'parameter_id':201, 'datetime': '2025', 'value': 10}, {'sensor_id':302, 'parameter_id':202, 'datetime': '2025', 'value': 20}]

        with patch('src.load.create_engine') as sql_mock:
            sql_mock.side_effect = exception
            with pytest.raises(expected_exception):
                load_postgres(location_record, parameter_record, sensor_record, measurement_record)

        assert expected_logs in caplog.text

    def test_load_orchestrator_latest_file_is_picked_numerically(self, tmp_path):
        file_1 = tmp_path/"measurements_2.csv"
        file_2 = tmp_path/"measurements_10.csv"

        file_1.touch()

        file_2.touch()


        with patch("src.load.DATA_DIR", tmp_path):
            with patch("src.load.read_from_csv") as mock_csv:
                with patch("src.load.load_postgres") as mock_load:
                    mock_csv.return_value = pd.DataFrame({
                        'location_id': [1],
                        'location_name': ['LocA'],
                        'parameter_id': [201],
                        'parameter_name': ['pm25'],
                        'parameter_unit':['ppb'],
                        'sensor_id': [301],
                        'datetime': [pd.Timestamp('2024-01-01')],
                        'value': [3]})

                    load_orchestrator()

                    mock_csv.assert_called_once_with(file_2)

                    mock_load.assert_called_once()

    def test_load_orchestrator_header_only_csv(self, caplog, tmp_path):
        caplog.set_level('INFO')

        file_name = tmp_path/"measurements_2.csv"

        fieldnames = ['location_id', 'location_name', 'sensor_id', 'value', 'parameter_id', 'parameter_name',
                      'parameter_unit', 'datetime']

        with open(file_name, mode='w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()

        with patch("src.load.DATA_DIR", tmp_path):
            with patch("src.load.load_postgres") as mock_load:
                result = load_orchestrator()

                assert result is None

                mock_load.assert_not_called()

        assert "No data found in csv. Incremental loading cannot start." in caplog.text

