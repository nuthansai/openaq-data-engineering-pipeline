from datetime import datetime
from sqlalchemy import text
from src.load import load_postgres


class TestIntegration():

    def test_practice_integration_3(self, connect_postgres):
        engine = connect_postgres

        location_record = [{'location_id': 101, 'location_name': 'locA'}, {'location_id': 102, 'location_name': 'locB'}]

        parameter_record = [{'parameter_id': 201, 'parameter_name': 'no', 'parameter_unit':'ppb'},
                            {'parameter_id': 202, 'parameter_name': 'co', 'parameter_unit':'ppb'}]

        sensor_record = [{'sensor_id': 301, 'location_id':101}, {'sensor_id': 302, 'location_id':102}]

        measurement_record = [{'sensor_id':301, 'parameter_id':201, 'datetime': datetime(2025,1,1), 'value':3.5},
                           {'sensor_id':302, 'parameter_id':202, 'datetime': datetime(2025,1,2), 'value':3.9}]

        load_postgres(location_record, parameter_record, sensor_record, measurement_record, engine)

        with engine.begin() as conn:
            loc_rows = conn.execute(text("SELECT * FROM locations")).mappings().all()

            par_rows = conn.execute(text("SELECT * FROM parameters")).mappings().all()

            sen_rows = conn.execute(text("SELECT * FROM sensors")).mappings().all()

            mes_rows = conn.execute(text("SELECT parameter_id, sensor_id, datetime, value FROM measurements")).mappings().all()

            assert loc_rows[:][:] == location_record

            assert par_rows[:][:] == parameter_record

            assert sen_rows[:][:] == sensor_record

            assert mes_rows[:][:] == measurement_record

