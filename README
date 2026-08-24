# OpenAQ Data Engineering Pipeline

A Python-based data engineering pipeline that extracts air-quality measurements from the OpenAQ API, transforms the data, stages it as CSV files, and loads it into PostgreSQL.

The project supports both an **initial historical extraction** and **incremental extraction**. Incremental runs use PostgreSQL as the source of truth to determine the latest measurement available for each sensor and parameter.

## Architecture

```text
                         Initial Historical Load

OpenAQ API
    │
    ▼
Extract locations & sensor measurements
    │
    ▼
Transform API responses
    │
    ▼
CSV staging files
    │
    ▼
PostgreSQL
```

For subsequent runs, the pipeline uses the database to determine where extraction should continue:

```text
PostgreSQL
    │
    │ MAX(datetime) per sensor/parameter
    ▼
Determine next extraction date
    │
    ▼
OpenAQ API
    │
    ▼
Transform measurements
    │
    ▼
CSV staging file
    │
    ▼
PostgreSQL
```

## Key Design Decisions

### PostgreSQL is the source of truth

The incremental pipeline does not use the latest CSV to determine which data should be extracted next.

For every sensor and parameter combination, the pipeline queries PostgreSQL for:

```sql
MAX(datetime)
```

The next extraction date is then calculated as:

```text
MAX(datetime) + 1 day
```

This means the pipeline can recover from previous runs based on the data actually loaded into PostgreSQL.

### CSV as an intermediate staging layer

CSV files are used as an intermediate artifact between extraction/transformation and database loading.

The CSV is not used to determine incremental state.

This separation allows the extraction and loading stages to remain independent. If a database load fails, the generated CSV can still be inspected or reused without having to retrieve the data from the API again.

## Pipeline Components

### API Extraction

The pipeline communicates directly with the OpenAQ API using Python's `requests` library.

The initial extraction retrieves historical measurements, while the incremental extraction determines the required date range from PostgreSQL and requests only the subsequent data.

API requests use an explicit timeout to prevent a slow request from blocking the pipeline indefinitely.

Requests are also deliberately spaced using a two-second delay to avoid rapid request bursts and reduce the likelihood of API rate-limit errors.

### Transformation

OpenAQ API responses are transformed into a consistent measurement structure containing fields such as:

* `location_id`
* `location_name`
* `sensor_id`
* `value`
* `parameter_id`
* `parameter_name`
* `parameter_unit`
* `datetime`

The transformed records are written to CSV files.

### CSV File Management

Incremental measurement files follow the naming convention:

```text
measurements_1.csv
measurements_2.csv
measurements_3.csv
...
```

The pipeline identifies the latest numbered file using `pathlib`.

If the latest CSV is empty, its file number can be reused. Otherwise, the next sequential file number is created.

### PostgreSQL Loading

The loader reads the latest measurement CSV and loads data into four PostgreSQL tables:

```text
locations
parameters
sensors
measurements
```

SQLAlchemy is used for database interaction.

The database inserts use PostgreSQL's `ON CONFLICT DO NOTHING` behavior to prevent duplicate records.

For measurements, the conflict key is:

```text
sensor_id + parameter_id + datetime
```

This provides protection against duplicate measurements both within repeated pipeline runs and when previously loaded data appears again in an incoming CSV.

Database operations are performed inside a transaction using SQLAlchemy's:

```python
with engine.begin() as conn:
```

If the transaction succeeds, the changes are committed. If an error occurs, the transaction is rolled back.

## Error Handling

The project distinguishes between expected/recoverable failures and unexpected failures.

Examples include:

* API timeout → logged and the sensor is skipped
* Network connection failure → logged and processing continues
* HTTP authentication failure → extraction is stopped
* Database/SQLAlchemy errors → logged and re-raised
* Unexpected exceptions → logged with traceback and re-raised

Python's built-in `logging` module is used throughout the project.

Each module creates its own logger using:

```python
logger = logging.getLogger(__name__)
```

Logging configuration is centralized so that extraction and loading modules use the same logging setup.

## Logging

Logs are written using Python's logging framework.

The log format contains:

```text
timestamp - module - level - message
```

For example:

```text
2026-08-24 14:30 - src.incremental.extract_incremental - INFO - Incremental extraction Started
```

Log files are configured using Python's rotating file-handler functionality so that log history does not remain in a single indefinitely growing file.

## Scheduling

The incremental pipeline is designed to run automatically using **Windows Task Scheduler**.

The scheduled process runs the pipeline entry point, which performs:

```text
Incremental extraction
        ↓
CSV creation
        ↓
PostgreSQL loading
```

The database determines the correct starting point for each incremental run, so the pipeline does not depend on manually specifying the next extraction date.

## Project Structure

A simplified structure is:

```text
project/
│
├── src/
│   ├── config.py
│   ├── logging_config.py
│   ├── load.py
│   ├── ...
│   └── incremental/
│       └── extract_incremental.py
│
├── main.py
├── data/
├── logs/
├── .env
├── .gitignore
└── requirements.txt
```

The exact project structure may contain additional modules for the historical extraction and transformation stages.

## Configuration

Sensitive configuration such as database credentials and API credentials is provided through environment variables rather than being hard-coded into the source code.

A `.env` file can be used locally.

Example:

```text
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=your_host
DB_NAME=your_database
```

The `.env` file should **not** be committed to GitHub.

## Installation

Clone the repository and create a Python virtual environment:

```bash
git clone <your-repository-url>
cd <your-repository>
```

Create and activate the virtual environment:

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Configure the required environment variables in `.env`.

Make sure PostgreSQL is available and the required database/tables have been created.

## Running the Pipeline

The pipeline entry point is:

```bash
python main.py
```

The incremental pipeline then:

```text
1. Connects to PostgreSQL
2. Finds MAX(datetime) for each sensor/parameter
3. Determines the next extraction date
4. Requests new measurements from OpenAQ
5. Transforms the API response
6. Writes the measurements to CSV
7. Loads the CSV into PostgreSQL
8. Prevents duplicate database records
9. Records execution details in the log
```

## Technologies Used

* **Python**
* **Requests** — OpenAQ API communication
* **Pandas** — data processing and transformation
* **PostgreSQL** — persistent data store
* **SQLAlchemy** — database connectivity and inserts
* **python-dotenv** — environment configuration
* **Python logging** — application logging
* **CSV** — intermediate staging format
* **Windows Task Scheduler** — scheduled execution

## What This Project Demonstrates

This project was built to practice the core concepts involved in developing a practical data pipeline:

* REST API data extraction
* Historical and incremental data ingestion
* API rate-limit management
* Data transformation
* File-based staging
* Relational database loading
* PostgreSQL conflict handling
* Transaction management
* Exception handling
* Structured application logging
* Database-driven incremental processing
* Automated scheduled execution

## Future Improvements

Potential future improvements include:

* Load statistics such as attempted, inserted, and duplicate rows
* More detailed monitoring of pipeline execution
* Additional analytical SQL queries for newly accumulated data
* Further improvements to retry and API failure handling

These are considered enhancements rather than prerequisites for the core pipeline.

## Data Source

This project uses data provided by the OpenAQ API.

OpenAQ documentation:

https://docs.openaq.org/
git