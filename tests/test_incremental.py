import csv
from unittest.mock import patch, Mock, MagicMock

import pandas as pd
import pytest
from requests.exceptions import Timeout,ConnectionError, HTTPError
from src.incremental.extract_incremental import incremental_extract
from sqlalchemy.exc import ArgumentError, SQLAlchemyError


class TestOpenAQ_incremental():
    @pytest.mark.parametrize('exception, expected_logs, expected_exception',[
            (ArgumentError("bad argument at construction time"), "Error: bad argument at construction time", ArgumentError),
            (SQLAlchemyError("Connection Failed"), "Database connection failed: Connection Failed", SQLAlchemyError)
        ])
    def test_extract_incremental_sql(self, exception, expected_logs, expected_exception):
        """
                Verify that database connection/engine errors raise expected exceptions
                and output appropriate error logs without proceeding to API extraction.
        """
        with patch('src.incremental.extract_incremental.create_engine') as sql_mock:
            with patch('src.incremental.extract_incremental.logger') as sql_mock_logger:
                sql_mock.side_effect = exception
                with pytest.raises(expected_exception):
                    incremental_extract()
                sql_mock_logger.exception.assert_called_once_with(expected_logs)


    @pytest.mark.parametrize('exception, sensor, expected_logs, expected_api_response',  [
        (Timeout("API call timed out"),
         87357,
         "Sensor 87357 timed out: API call timed out",
         [{"value": 0.515, "parameter": {"id": 201, "name": "no", "units": "ppb"}, "period": {"datetimeFrom": {"utc": "2025-02-18T18:30:00Z", "local": "2025-02-19T00:00:00+05:30"},	"datetimeTo": {	"utc": "2025-02-19T18:30:00Z", "local": "2025-02-20T00:00:00+05:30"}}}]
         )
    ])
    def test_extract_incremental_api(self, caplog, tmp_path, exception, sensor, expected_logs, expected_api_response):
        """
                Verify pipeline resilience when an API call fails for a single sensor.

                Tests that:
                1. Non-failing sensors continue processing and write enriched rows to CSV.
                2. Failing sensor exceptions are caught and logged gracefully.
                3. All database records are processed (loop resiliency verified by call count).
        """
        caplog.set_level("WARNING")

        with patch('src.incremental.extract_incremental.create_engine') as mock_create_engine:
            mock_engine = MagicMock()
            mock_create_engine.return_value = mock_engine

            df_fake = pd.DataFrame([
                {'location_id': 101, 'location_name': 'Srikakulam', 'sensor_id': 87356, 'parameter_id': 201, 'parameter_name': 'no', 'max_date': pd.Timestamp('2025-01-01')},
                {'location_id': 102, 'location_name': 'Vishakapatnam', 'sensor_id': 87357, 'parameter_id': 202, 'parameter_name': 'co', 'max_date': pd.Timestamp('2025-01-02')},
                {'location_id': 103, 'location_name': 'Vizianagaram', 'sensor_id': 87358, 'parameter_id': 201, 'parameter_name': 'no2', 'max_date': pd.Timestamp('2025-01-03')}
            ])

            with patch('src.incremental.extract_incremental.pd.read_sql', return_value = df_fake) as df_sql_mock:
                with patch('src.incremental.extract_incremental.DATA_DIR', tmp_path):
                    def fake_get(url, headers=None, timeout=None):
                        if f"/sensors/{sensor}/days" in url:
                            raise exception
                        return Mock(status_code=200, json = lambda: {"results": expected_api_response})
                    with patch('src.incremental.extract_incremental.requests.get', side_effect = fake_get) as get_mock:
                        incremental_extract()


                        generated_files = list(tmp_path.glob('*.csv'))
                        assert len(generated_files) == 1
                        test_file = generated_files[0]
                        assert test_file.exists()

                        with test_file.open("r", encoding="utf-8") as f:
                            reader = list(csv.DictReader(f))

                            assert len(reader) == 2

                            assert reader[0] == {'location_id': '101', 'location_name': 'Srikakulam', 'sensor_id': '87356', 'value': '0.515', 'parameter_id': '201', 'parameter_name': 'no', 'parameter_unit': 'ppb', 'datetime': '2025-02-19T00:00:00+05:30'}
                            assert reader[1] == {'location_id': '103', 'location_name': 'Vizianagaram', 'sensor_id': '87358', 'value': '0.515', 'parameter_id': '201', 'parameter_name': 'no', 'parameter_unit': 'ppb', 'datetime': '2025-02-19T00:00:00+05:30'}

                            assert get_mock.call_count == 3




        assert expected_logs in caplog.text