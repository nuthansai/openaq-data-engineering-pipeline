# OpenAQ Data Engineering Pipeline

A Python-based data engineering project for collecting, transforming, loading, and analyzing air-quality measurements from the OpenAQ API into PostgreSQL. The repository includes:

- an initial historical extraction workflow
- an incremental extraction workflow based on the latest database state
- CSV staging for intermediate data storage
- PostgreSQL schema and data-quality views
- a Streamlit dashboard for air-quality analysis

## Overview

This project ingests air-quality data from OpenAQ for monitoring stations across India. It stores the information in PostgreSQL and makes it available for downstream analysis, reporting, and dashboarding.

The workflow follows a common data engineering pattern:

1. Extract data from an external API
2. Transform raw API responses into a consistent structure
3. Write intermediate CSV files
4. Load data into PostgreSQL
5. Query the database for analysis and reporting
6. Visualize trends via Streamlit

## Architecture

```text
OpenAQ API
    │
    ▼
Extract locations and measurement data
    │
    ▼
Transform records into normalized data model
    │
    ▼
Write CSV staging files
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
Run SQL analysis / dashboard queries
```

### Incremental extraction design

The pipeline does not use the latest CSV as the source of truth for its next run. Instead, it queries PostgreSQL to find the latest timestamp per sensor and parameter combination, and then requests only new data after that point.

This approach allows the pipeline to resume safely after interruptions and avoids depending on temporary CSV state.

## Key features

- API extraction from OpenAQ using Python `requests`
- Historical initial load and incremental refresh logic
- PostgreSQL as the persistent source of truth
- CSV-based staging before database inserts
- Duplicate prevention using database conflict logic
- Logging and exception handling for API and database failures
- SQL analysis views for filtered pollutant and meteorological datasets
- Streamlit dashboard for air-quality exploration

## Repository structure

```text
openaq-data-engineering-pipeline/
├── .gitignore
├── main.py
├── README.md
├── dashboard/
│   └── app.py
├── sql/
│   ├── create_tables.sql
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
│   ├── test_incremental.py
│   └── test_initial.py
├── Data/                 # generated at runtime
├── log/                  # generated at runtime
└── .env                  # local environment configuration
```

## Tech stack

- Python
- `requests` for API calls
- `pandas` for transformation and CSV handling
- `SQLAlchemy` for DB interactions
- PostgreSQL for storage and analysis
- `python-dotenv` for environment variables
- `Streamlit` for dashboarding
- `pytest` for testing

## Prerequisites

Before running the project, make sure you have:

- Python 3.10+
- PostgreSQL installed and running
- A valid OpenAQ API key
- Access to a local or remote PostgreSQL database

## Environment configuration

Create a `.env` file in the project root with the required variables:

```env
OPENAQ_API_KEY=your_openaq_api_key
DB_HOST=localhost
DB_USER=postgres
DB_PASSWORD=your_password
DB_NAME=your_database
```

The project reads these settings in `src/config.py` using `python-dotenv`.

## Database setup

The schema is defined in `sql/create_tables.sql`.

Run the SQL file against your PostgreSQL database before the first load:

```bash
psql -U postgres -d your_database -f sql/create_tables.sql
```

The schema includes:

- `locations`
- `parameters`
- `sensors`
- `measurements`

## Installation

Clone the repository:

```bash
git clone https://github.com/nuthansai/openaq-data-engineering-pipeline.git
cd openaq-data-engineering-pipeline
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```bash
.venv\Scripts\activate
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

If a `requirements.txt` file is not present in the repo, install the commonly required packages manually:

```bash
pip install requests pandas sqlalchemy python-dotenv streamlit pytest
```

## Running the pipeline

The main entry point is:

```bash
python main.py
```

`main.py` triggers the incremental extraction and then loads the generated CSV file into PostgreSQL:

```python
from src.load import load_orchestrator
from src.incremental.extract_incremental import run_incremental_extract
import src.logging_config


def main():
    run_incremental_extract()
    load_orchestrator()
```

This means the pipeline:

1. looks up the latest data in PostgreSQL
2. determines the next extraction window
3. fetches new measurements from OpenAQ
4. writes results to a CSV file
5. loads them into database tables

## Dashboard

The project includes a Streamlit dashboard for exploring the loaded data:

```bash
streamlit run dashboard/app.py
```

This dashboard includes:

- dataset overview KPIs
- monthly pollutant trend charts
- top polluted locations
- pollutant comparison views
- seasonal pollution summaries

## SQL analysis and data quality

The SQL scripts under `sql/` contain analysis and cleaning logic, including:

- creating clean pollutant and meteorological views
- identifying negative or abnormal values
- exploring trends and location-level insights
- comparing pollution by season, parameter, and geography

Examples include:

- `clean_pollutants`
- `clean_meteorological`
- summary queries for PM2.5, NO2, humidity, wind, and temperature

This is especially important because the dataset contains quality issues such as negative values, which are filtered for analysis.

## Testing

The repository contains unit tests for both initial and incremental workflows:

```bash
pytest tests/
```

These tests cover the main extraction and transformation logic and help validate the pipeline behavior.

## Logging

The project uses Python’s `logging` module to capture application events, API failures, and database errors. Logs are stored under the `log/` directory.

## Notes

- `.env` should not be committed to GitHub.
- Generated runtime folders such as `Data/` and `log/` are ignored by Git.
- The pipeline is designed to be schedulable for regular updates, such as via Windows Task Scheduler or cron.
- The dashboard expects the PostgreSQL database to already contain cleaned and loaded analysis data.

## What this project demonstrates

This repository is a practical example of:

- API-driven data ingestion
- incremental ELT processing
- PostgreSQL modeling and loading
- data cleaning and validation
- analytical SQL
- dashboard-based business intelligence
- end-to-end data engineering workflow design

## Future improvements

Potential next steps for the project include:

- richer load metrics and row counts
- retry policies for API rate limits
- automated scheduling and orchestration
- more robust validation and alerting
- deployment packaging and environment automation

## Data source

This project uses OpenAQ API data.

Documentation: https://docs.openaq.org/

