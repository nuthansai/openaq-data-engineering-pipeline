from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from src.load import load_postgres

from src.sql_models import locations, sensors, parameters, measurements


class TestIntegration():
    def ptest_practice_integration_1(self, connect_postgres):
        engine = connect_postgres



        # load
        with engine.begin() as conn:

            stmt = insert(locations).values({'location_id': 101, 'location_name': 'locA'})

            conn.execute(stmt)

        with engine.begin() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM locations"))
            count = result.scalar()  # fetches the single count value

            assert count == 1

    def ptest_practice_integration_2(self, connect_postgres):
        engine = connect_postgres

        records = [{'location_id': 101, 'location_name': 'locA'}, {'location_id': 102, 'location_name': 'locB'}]
        with engine.begin() as conn:

            stmt = insert(locations).values(records)
            conn.execute(stmt)


        with engine.begin() as conn:
            rows = conn.execute(text("SELECT * FROM locations"))
            count = rows.mappings().all()

            print(count)

            assert count[0]['location_id'] == 101


    def ptest_practice_integration_3(self, connect_postgres):
        engine = connect_postgres

        location_record = [{'location_id': 101, 'location_name': 'locA'}, {'location_id': 102, 'location_name': 'locB'}]

        parameter_record = [{'parameter_id': 201, 'parameter_name': 'no', 'parameter_unit':'ppb'},
                            {'parameter_id': 202, 'parameter_name': 'co', 'parameter_unit':'ppb'}]

        sensor_record = [{'sensor_id': 301, 'location_id':101}, {'sensor_id': 302, 'location_id':102}]

        measurement_record = [{'sensor_id':301, 'parameter_id':201, 'datetime':'2026-01-01', 'value':3.5},
                           {'sensor_id':302, 'parameter_id':202, 'datetime':'2026-01-02', 'value':3.9}]

        load_postgres(location_record, parameter_record, sensor_record, measurement_record, engine)

        with engine.begin() as conn:

            loc_stmt = insert(locations).values({'location_id': 101, 'location_name': 'locA'})
            do_nothing_loc = loc_stmt.on_conflict_do_nothing(index_elements = ["location_id"])
            conn.execute(do_nothing_loc)

            par_stmt = insert(parameters).values({'parameter_id': 201, 'parameter_name': 'no', 'parameter_unit':'ppb'})
            do_nothing_par = par_stmt.on_conflict_do_nothing(index_elements=['parameter_id'])
            conn.execute(do_nothing_par)

            sensor_stmt = insert(sensors).values({'sensor_id': 301, 'location_id':101})
            do_nothing_sensor = sensor_stmt.on_conflict_do_nothing(index_elements=["sensor_id"])
            conn.execute(do_nothing_sensor)

            mes_records = [{'sensor_id':301, 'parameter_id':201, 'datetime':'2026-01-01', 'value':3},
                           {'sensor_id':301, 'parameter_id':201, 'datetime':'2026-01-01', 'value':3}]
            mes_stmt = insert(measurements).values(mes_records)
            do_nothing_mes = mes_stmt.on_conflict_do_nothing(index_elements=['sensor_id', 'parameter_id', 'datetime'])
            conn.execute(do_nothing_mes)

        with engine.begin() as conn:
            rows = conn.execute(text("SELECT COUNT(*) FROM measurements")).scalar()
            assert rows == 1