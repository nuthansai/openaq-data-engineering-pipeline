# OpenAQ Data Engineering Pipeline

A Python data engineering project that collects air-quality measurements from the OpenAQ API, stages them as CSV files, loads them into a normalized PostgreSQL database, and exposes them through SQL analysis views and a Streamlit dashboard. The whole stack runs in Docker, and the Python code can also be run locally with `uv`.

## Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Key features](#key-features)
- [Repository structure](#repository-structure)
- [Tech stack](#tech-stack)
- [Environment configuration](#environment-configuration)
- [Run with Docker](#run-with-docker)
- [Local development without Docker](#local-development-without-docker)
- [Running the pipeline](#running-the-pipeline)
- [Dashboard](#dashboard)
- [Database schema](#database-schema)
- [SQL analysis and data quality](#sql-analysis-and-data-quality)
- [Testing](#testing)
- [Logging](#logging)
- [Design notes and limitations](#design-notes-and-limitations)
- [What this project demonstrates](#what-this-project-demonstrates)
- [Future improvements](#future-improvements)
- [Data source](#data-source)

## Overview

This project ingests air-quality data from OpenAQ for monitoring stations across India and stores it in PostgreSQL for analysis, reporting and dashboarding.

The workflow follows a common data engineering pattern:

1. Extract data from an external API
2. Transform raw API responses into a consistent structure
3. Write intermediate CSV files (staging)
4. Load the data into PostgreSQL
5. Query the database for analysis and reporting
6. Visualize trends in Streamlit

The repository contains two workflows:

- **Initial (historical) load** in `src/initial/`: explores the API, extracts locations and sensors, downloads historical measurements and transforms them.
- **Incremental load** in `src/incremental/`: finds the latest data already in PostgreSQL and fetches only what is newer. This is what `main.py` runs.

## Architecture

```text
OpenAQ API
    │
    ▼
Extract locations and measurement data
    │
    ▼
Transform records into a normalized data model
    │
    ▼
Write CSV staging files (Data/measurements_N.csv)
    │
    ▼
Load into PostgreSQL
    │
    ├── locations
    ├── parameters
    ├── sensors
    └── measurements
    │
    ▼
SQL analysis views / Streamlit dashboard
```

### Incremental extraction design

The pipeline does not use the latest CSV as the source of truth for its next run. It queries PostgreSQL for the latest `datetime` per sensor and parameter and requests only data after that point (from the following day onward, using the OpenAQ daily endpoint).

This lets the pipeline resume safely after interruptions and avoids depending on temporary CSV state.

Failure handling during extraction:

- `401`, `403` and `429` responses stop the run (bad key, no access, rate limit). The next run resumes from the database state.
- Timeouts, connection errors and other HTTP errors skip that sensor and continue.
- A short pause between requests avoids bursts that trigger rate limits.

### Idempotent loading

Rows are inserted with `ON CONFLICT DO NOTHING`, backed by a unique key on `(sensor_id, parameter_id, datetime)`. Each CSV is loaded in a single transaction, so a failed load leaves no partial data, and re-loading the same file creates no duplicates.

## Key features

- API extraction from OpenAQ using Python `requests`
- Historical initial load and incremental refresh logic
- PostgreSQL as the persistent source of truth
- CSV-based staging before database inserts
- Duplicate prevention through a unique key and conflict handling
- Load summaries (attempted, inserted, duplicates) logged per table
- Logging and exception handling for API and database failures
- SQL analysis views for pollutant and meteorological data
- Streamlit dashboard for air-quality exploration
- Unit tests plus PostgreSQL integration tests
- Multi-stage Docker images and a Compose setup for the database, pgAdmin, ETL and dashboard

## Repository structure

```text
openaq-data-engineering-pipeline/
├── .dockerignore
├── .gitignore
├── .python-version
├── Dockerfile                 # multi-stage: base, etl-runner, dashboard
├── README.md
├── docker-compose.yaml        # database, pgAdmin, ETL, dashboard, test database
├── main.py                    # entry point: incremental extract, then load
├── pyproject.toml             # dependencies (uv)
├── pytest.ini
├── uv.lock                    # locked dependency versions
├── dashboard/
│   └── app.py
├── sql/
│   ├── create_tables.sql      # schema, run automatically on first database start
│   └── sql_analysis.sql
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── load.py
│   ├── logging_config.py
│   ├── sql_models.py
│   ├── initial/
│   │   ├── __init__.py
│   │   ├── explore_api.py
│   │   ├── extract_locations.py
│   │   ├── get_measurements.py
│   │   └── transform_measurements.py
│   └── incremental/
│       ├── __init__.py
│       └── extract_incremental.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # test database fixture
│   ├── test_db_integration.py
│   ├── test_incremental.py
│   ├── test_initial.py
│   └── test_load.py
├── Data/                      # generated at runtime, ignored by Git
├── log/                       # generated at runtime, ignored by Git
└── .env                       # local configuration, never committed
```

## Tech stack

- Python 3.12
- `requests` for API calls
- `pandas` for transformation and CSV handling
- `SQLAlchemy` 2.0 with `psycopg2` for database access
- PostgreSQL 17
- `python-dotenv` for environment variables
- Streamlit for the dashboard
- `pytest` for testing
- `uv` for dependency management
- Docker and Docker Compose; pgAdmin for querying the database

## Environment configuration

Create a `.env` file in the project root (next to `docker-compose.yaml`):

```env
OPENAQ_API_KEY=your_openaq_api_key
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_HOST=127.0.0.1
DB_PORT=5432
```

- Docker Compose uses `DB_USER`, `DB_PASSWORD` and `DB_NAME` to create the database the first time it starts.
- `DB_HOST=127.0.0.1` is for code running on your machine. The ETL and dashboard containers override it with `DB_HOST=postgres_main_openaq`, because inside a container `localhost` is the container itself.
- `.env` is excluded from the Docker images by `.dockerignore`. Settings reach the containers at runtime through `env_file`.
- You need a valid OpenAQ API key (see https://docs.openaq.org/).

## Run with Docker

Docker is the quickest way to run everything. You need only Docker (with Compose v2) and a `.env` file. No local Python or `uv` is required.

### Quick start

```bash
git clone https://github.com/nuthansai/openaq-data-engineering-pipeline.git
cd openaq-data-engineering-pipeline

# create .env as described above

docker compose build
docker compose up -d
docker compose ps          # wait until postgres_main_openaq is healthy
```

<<<<<<< HEAD
Open the dashboard at http://localhost:8501 and pgAdmin at http://localhost:8085.

> **A fresh database starts with tables but no data.** The incremental pipeline continues from data that already exists in PostgreSQL, so on an empty database it has nothing to continue from. The historical load scripts in `src/initial/` are not part of the Docker flow. Load the historical data first, then run the incremental pipeline.

### Services

| Service | Purpose | Host port | Starts with |
|---|---|---|---|
| `postgres_main_openaq` | Main PostgreSQL 17 database (persistent volume, healthcheck) | 5432 | `docker compose up -d` |
| `pgadmin_openaq` | pgAdmin web UI for querying the databases | 8085 | `docker compose up -d` |
| `open_aq_dashboard` | Streamlit dashboard | 8501 | `docker compose up -d` |
| `open_aq_etl` | Incremental extract and load (`main.py`), runs once and exits | none | on demand (profile `app`) |
| `postgres_integration_test_openaq` | Throwaway PostgreSQL 17 for integration tests, no volume | 5433 | on demand (profile `test`) |

### Images (`Dockerfile`)

One Dockerfile with three stages:

- `base`: `python:3.12.10-slim` plus `uv`. Installs the locked runtime dependencies only (`uv sync --locked --no-dev`) and creates a non-root `app` user.
- `etl-runner`: copies the code and runs `python main.py`.
- `dashboard`: copies the code and runs Streamlit on port 8501.

`Data/` and `log/` are created inside the containers and are not mounted by default, so staging CSVs and logs written by a container are lost when it is removed. Mount `./Data:/OPENAQ/Data` on the ETL service if you want to keep them.

### Common commands

```bash
# Build the images
docker compose build

# Start the database, pgAdmin and dashboard
docker compose up -d

# Run the pipeline once (incremental extract, then load)
docker compose run --rm open_aq_etl

# Start the integration-test database
docker compose up -d postgres_integration_test_openaq

# Stop everything (data is kept)
docker compose down
```

### Connecting pgAdmin to the databases

pgAdmin runs inside Docker, so register servers by service name and container port:

| Database | Host | Port | Credentials |
|---|---|---|---|
| Main | `postgres_main_openaq` | 5432 | `DB_USER` and `DB_PASSWORD` from `.env`, database `DB_NAME` |
| Integration test | `postgres_integration_test_openaq` | 5432 | `root` / `root`, database `practice_integration` |

Use the container port (5432), not the published host port.

### Data persistence

- The main database lives in the named volume `postgres_data` (`openaq_postgres_data` on disk, because the Compose project name is pinned to `openaq`). It survives `docker compose down`, restarts and image rebuilds.
- `docker compose down -v` deletes the volumes and all data. Do not use `-v` unless you want a clean slate.
- `sql/create_tables.sql` runs automatically only on the first start, while the volume is empty. Later edits to it do not re-run on an existing volume.
- `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` are applied only when the volume is first created. If you change `DB_USER`, `DB_PASSWORD` or `DB_NAME` afterwards, the existing database keeps the old values until you reset the volume.
- The incremental extract reads its starting point from the database, not from CSV files, so an empty `Data/` folder in a fresh container is fine.

### Troubleshooting

- **Authentication failed:** compare `.env` with the credentials the volume was created with (`docker compose config` shows what Compose substitutes) and remember the first-start rule above.
- **Port already in use:** another process or container owns 5432, 5433, 8085 or 8501. Check with `docker ps` and stop it.
- **`ModuleNotFoundError` in a container:** imports must use the `src.` prefix (for example `from src.config import ...`), because only the project root is on the path inside the image.
- **Code changes not visible in a container:** code is copied into the image at build time, so run `docker compose build` again.
- **`network ... Resource is still in use` on `down`:** a leftover container is attached. Find it with `docker ps -a --filter network=openaq_default` and remove it.

## Local development without Docker

Use this route to develop, debug and run tests from your machine.

Prerequisites:

- Python 3.12+ (uv can install it for you)
- [`uv`](https://docs.astral.sh/uv/)
- A reachable PostgreSQL database with the schema from `sql/create_tables.sql`. The simplest option is the Compose database:

```bash
docker compose up -d postgres_main_openaq
```

With the Compose database, keep `DB_HOST=127.0.0.1` and `DB_PORT=5432` in `.env`.

Install the project and its dependencies (runtime and dev) from the lock file:
=======
This project uses `uv` for dependency management and virtual environment setup.

Install the project and its dependencies:

```bash
uv sync --group dev
```

This creates a managed virtual environment and installs the dependencies from `pyproject.toml`.

If you want to activate the environment manually:
>>>>>>> d287d8bee6c77da6cbdd7f779bbf07d82d064550

```bash
uv sync
```

<<<<<<< HEAD
Run commands inside the managed environment:

```bash
uv run python main.py
uv run pytest
uv run streamlit run dashboard/app.py
```

If you use your own PostgreSQL instead, create the schema first:

```bash
psql -U <user> -d <database> -f sql/create_tables.sql
=======
On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

To run commands inside the project environment without activating it manually, use:

```bash
uv run python main.py
uv run pytest tests/
uv run streamlit run dashboard/app.py
>>>>>>> d287d8bee6c77da6cbdd7f779bbf07d82d064550
```

The project uses the environment variables defined in `.env`; create that file first as described in the Configuration section.

## Running the pipeline

`main.py` runs the incremental extraction and then loads the generated CSV into PostgreSQL:

```python
from src.load import load_orchestrator
from src.incremental.extract_incremental import run_incremental_extract
import src.logging_config


def main():
    run_incremental_extract()
    load_orchestrator()
```

Each run:

1. looks up the latest `datetime` per sensor and parameter in PostgreSQL
2. requests newer measurements from OpenAQ
3. writes them to the next `Data/measurements_N.csv`
4. loads the newest CSV into the four tables, logging attempted, inserted and duplicate counts

Run it with Docker (`docker compose run --rm open_aq_etl`) or locally (`uv run python main.py`).

## Dashboard

A Streamlit dashboard for exploring the loaded data:

```bash
# Docker: starts with `docker compose up -d`, then open http://localhost:8501
# Local:
uv run streamlit run dashboard/app.py
```

It includes dataset overview KPIs, monthly pollutant trends, top polluted locations, pollutant comparison views and seasonal pollution summaries.

The dashboard is a static snapshot of the database: it reflects the data as of the last pipeline run and does not refresh on its own. It expects the PostgreSQL database to already contain loaded data.

## Database schema

Defined in `sql/create_tables.sql`:

- `locations(location_id, location_name)`
- `parameters(parameter_id, parameter_name, parameter_unit)`
- `sensors(sensor_id, location_id)` with a foreign key to `locations`
- `measurements(measurement_id, sensor_id, parameter_id, datetime, value)` with foreign keys to `sensors` and `parameters`, and `UNIQUE (sensor_id, parameter_id, datetime)`

## SQL analysis and data quality

The scripts under `sql/` contain analysis and cleaning logic:

- clean pollutant and meteorological views (`clean_pollutants`, `clean_meteorological`)
- identifying negative or abnormal values
- trends and location-level insights
- comparisons by season, parameter and geography
- summary queries for PM2.5, NO2, humidity, wind and temperature

The dataset contains quality issues such as negative values, which are filtered for analysis.

## Testing

```bash
uv run pytest -m "not integration"    # unit tests, no database needed
uv run pytest -m integration          # database integration tests
```

**Unit tests** cover the initial extraction, the incremental extraction (including the `write_to_csv` error handling) and the load module (`read_from_csv`, `load_postgres` error branches and `load_orchestrator`). Mocks are used only at true boundaries (HTTP calls, the database engine), patched where a name is used.

**Integration tests** (`tests/test_db_integration.py`, marked `@pytest.mark.integration`) run against a real PostgreSQL 17 container with tables built from `sql/create_tables.sql`. They cover:

- first load
- reloading the same data (idempotency)
- partial overlap between loads
- rollback when a foreign-key constraint fails, leaving the tables empty

Start the test database with `docker compose up -d postgres_integration_test_openaq` (host port 5433) before running them.

### Deliberately skipped tests

- **Generic `except Exception` branches:** these only log and re-raise, so there is no distinct behavior to assert beyond the specific exception handlers that are tested.
- **`sensor_transformation`:** a straightforward mapping of API response fields into records.
- **`load_orchestrator` tests 9, 10 and 11:** they exercise the record-building logic, which the integration tests already cover end to end.
- **`read_from_csv` with a valid CSV:** a thin wrapper over `pandas.read_csv`; only its failure path is tested.

## Logging

The project uses Python's `logging` module to capture application events, API failures and database errors, including per-table load summaries. Logs are written under the `log/` directory.

## Design notes and limitations

- **Scheduling is off.** The pipeline is safe to run on a schedule because every run is idempotent. If scheduling is re-enabled, cron on Linux or WSL is the plan, not Windows Task Scheduler. For now, run the ETL manually.
- **Static dashboard.** The dashboard shows a snapshot and is not live.
- **Table growth.** `measurements` grows with every incremental run. The unique key on `(sensor_id, parameter_id, datetime)` also maintains an index, so storage grows faster than the row count alone. At larger scale, consider partitioning by `datetime`.
- **Local-development credentials.** The credentials in `docker-compose.yaml` for the test database and pgAdmin (`root`, `admin@admin.com`) are for local use only, and the database, pgAdmin and dashboard ports are published on all network interfaces. Do not expose this setup on an untrusted network as it is.
- **Secrets.** `.env` must never be committed. Runtime folders `Data/` and `log/` are ignored by Git.

## What this project demonstrates

- API-driven data ingestion
- incremental ELT processing with idempotent loads
- PostgreSQL modeling and loading
- data cleaning and validation in SQL
- analytical SQL and dashboard-based reporting
- unit and database integration testing
- reproducible environments with `uv` and Docker
- end-to-end data engineering workflow design

## Future improvements

- re-enable scheduling and add orchestration
- a live dashboard that reads directly from PostgreSQL
- retry policies for API rate limits
- richer load metrics and row counts
- more robust validation and alerting

## Data source

This project uses OpenAQ API data. Documentation: https://docs.openaq.org/
