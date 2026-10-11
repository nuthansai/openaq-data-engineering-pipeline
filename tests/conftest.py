from pathlib import Path

import pytest
from sqlalchemy import URL, create_engine, text


@pytest.fixture(scope='class')
def connect_postgres():
    url = URL.create(
        drivername='postgresql',
        username='root',
        password='root',
        host='localhost',
        database='practice_integration',
        port=5432
    )

    engine = create_engine(url)

    root_path = Path(__file__).parent.parent
    sql_path = root_path / "sql" / "create_tables.sql"
    ddl_script = sql_path.read_text()

    with engine.begin() as conn:

        conn.execute(
            text(
                "DROP TABLE IF EXISTS measurements, sensors, parameters, locations"
                " CASCADE;"
            )
        )

        conn.execute(text(ddl_script))

    yield engine