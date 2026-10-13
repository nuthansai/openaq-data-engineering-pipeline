import pytest
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.load import load_postgres


@pytest.mark.integration
class TestIntegration():

    location_record = [{'location_id': 101, 'location_name': 'locA'}, {'location_id': 102, 'location_name': 'locB'}]

    parameter_record = [{'parameter_id': 201, 'parameter_name': 'no', 'parameter_unit': 'ppb'},
                        {'parameter_id': 202, 'parameter_name': 'co', 'parameter_unit': 'ppb'}]

    sensor_record = [{'sensor_id': 301, 'location_id': 101}, {'sensor_id': 302, 'location_id': 102}]

    measurement_record = [{'sensor_id': 301, 'parameter_id': 201, 'datetime': datetime(2025, 1, 1), 'value': 3.5},
                          {'sensor_id': 302, 'parameter_id': 202, 'datetime': datetime(2025, 1, 2), 'value': 3.9}]

    locations_query = "SELECT * FROM locations"
    parameters_query = "SELECT * FROM parameters"
    sensors_query = "SELECT * FROM sensors"
    measurements_query = "SELECT parameter_id, sensor_id, datetime, value FROM measurements"

    def test_db_integration_first_load(self, connect_postgres):
        engine = connect_postgres

        load_postgres(self.location_record, self.parameter_record, self.sensor_record, self.measurement_record, engine)

        with engine.begin() as conn:
            loc_rows = conn.execute(text(self.locations_query)).mappings().all()

            par_rows = conn.execute(text(self.parameters_query)).mappings().all()

            sen_rows = conn.execute(text(self.sensors_query)).mappings().all()

            mes_rows = conn.execute(text(self.measurements_query)).mappings().all()

            assert loc_rows == self.location_record

            assert par_rows == self.parameter_record

            assert sen_rows == self.sensor_record

            assert mes_rows == self.measurement_record

    def test_db_integration_reload_the_same_data(self, connect_postgres):
        engine = connect_postgres

        # initial insert
        load_postgres(self.location_record, self.parameter_record, self.sensor_record, self.measurement_record, engine)

        with engine.begin() as conn:
            loc_rows_1 = conn.execute(text(self.locations_query)).mappings().all()
            loc_insert_count = len(loc_rows_1)

            par_rows_1 = conn.execute(text(self.parameters_query)).mappings().all()
            par_insert_count = len(par_rows_1)

            sen_rows_1 = conn.execute(text(self.sensors_query)).mappings().all()
            sen_insert_count = len(sen_rows_1)

            mes_rows_1 = conn.execute(text(self.measurements_query)).mappings().all()
            mes_insert_count = len(mes_rows_1)

        # second insert
        load_postgres(self.location_record, self.parameter_record, self.sensor_record, self.measurement_record, engine)

        with engine.begin() as conn:
            loc_rows_2 = conn.execute(text(self.locations_query)).mappings().all()

            par_rows_2 = conn.execute(text(self.parameters_query)).mappings().all()

            sen_rows_2 = conn.execute(text(self.sensors_query)).mappings().all()


            mes_rows_2 = conn.execute(text(self.measurements_query)).mappings().all()

            assert len(loc_rows_2) == loc_insert_count

            assert len(par_rows_2) == par_insert_count

            assert len(sen_rows_2) == sen_insert_count

            assert len(mes_rows_2) == mes_insert_count

    def test_db_integration_partial_overlap(self, connect_postgres):
        engine = connect_postgres


        load_postgres(self.location_record, self.parameter_record, self.sensor_record, self.measurement_record, engine)

        with engine.begin() as conn:
            conn.execute(text(self.locations_query)).mappings().all()

            conn.execute(text(self.parameters_query)).mappings().all()

            conn.execute(text(self.sensors_query)).mappings().all()

            conn.execute(text(self.measurements_query)).mappings().all()

        location_record_2 = self.location_record + [{'location_id': 103, 'location_name': 'locC'}]
        parameter_record_2 = self.parameter_record + [{'parameter_id': 203, 'parameter_name': 'no2', 'parameter_unit': 'ppb'}]
        sensor_record_2 = self.sensor_record + [{'sensor_id': 303, 'location_id': 103}]
        measurement_record_2 = self.measurement_record + [{'sensor_id': 303, 'parameter_id': 203,
                                                           'datetime': datetime(2025, 1, 3), 'value': 4.5}]

        load_postgres(location_record_2, parameter_record_2, sensor_record_2, measurement_record_2, engine)

        with engine.begin() as conn:
            loc_rows_2 = conn.execute(text(self.locations_query)).mappings().all()

            par_rows_2 = conn.execute(text(self.parameters_query)).mappings().all()

            sen_rows_2 = conn.execute(text(self.sensors_query)).mappings().all()

            mes_rows_2 = conn.execute(text(self.measurements_query)).mappings().all()

            assert len(loc_rows_2) == 3

            assert len(par_rows_2) == 3

            assert len(sen_rows_2) == 3

            assert len(mes_rows_2) == 3


    # referencing a missing sensor so the insert would fail and engine.begin() rollbacks
    def test_db_integration_failure_mid_load(self, connect_postgres):
        engine = connect_postgres

        load_postgres(self.location_record, self.parameter_record, self.sensor_record, self.measurement_record, engine)

        with engine.begin() as conn:
            conn.execute(text(self.locations_query)).mappings().all()

            conn.execute(text(self.parameters_query)).mappings().all()

            conn.execute(text(self.sensors_query)).mappings().all()

            conn.execute(text(self.measurements_query)).mappings().all()

        location_record_2 = self.location_record + [{'location_id': 103, 'location_name': 'locC'}]
        parameter_record_2 = self.parameter_record + [
            {'parameter_id': 203, 'parameter_name': 'no2', 'parameter_unit': 'ppb'}]
        sensor_record_2 = self.sensor_record + [{'sensor_id': 303, 'location_id': 103}]

        measurement_record_2 = self.measurement_record + [{'sensor_id': 304, 'parameter_id': 203,
                                                           'datetime': datetime(2025, 1, 3), 'value': 4.5}]

        with pytest.raises(IntegrityError):
            load_postgres(location_record_2, parameter_record_2, sensor_record_2, measurement_record_2, engine)

        with engine.begin() as conn:
            loc_rows_2 = conn.execute(text(self.locations_query)).mappings().all()

            par_rows_2 = conn.execute(text(self.parameters_query)).mappings().all()

            sen_rows_2 = conn.execute(text(self.sensors_query)).mappings().all()

            mes_rows_2 = conn.execute(text(self.measurements_query)).mappings().all()

            assert len(loc_rows_2) == 2

            assert len(par_rows_2) == 2

            assert len(sen_rows_2) == 2

            assert len(mes_rows_2) == 2