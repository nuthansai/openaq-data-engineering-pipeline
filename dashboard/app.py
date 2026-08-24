import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

engine = create_engine(f"postgresql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}")

import streamlit as st
import pandas as pd
from sqlalchemy import text


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Air Quality Dashboard",
    page_icon="🌍",
    layout="wide"
)


# --------------------------------------------------
# Title
# --------------------------------------------------

st.title("🌍 Air Quality Dashboard")

st.markdown(
    """
    Interactive analysis of air-quality measurements collected
    from monitoring locations across India using OpenAQ data.

    **Database:** PostgreSQL &nbsp;&nbsp;|&nbsp;&nbsp;
    **Analysis:** SQL &nbsp;&nbsp;|&nbsp;&nbsp;
    **Interface:** Streamlit
    """
)

st.divider()


# --------------------------------------------------
# KPI SECTION
# --------------------------------------------------

st.subheader("Dataset Overview")

query = """
SELECT
    (SELECT COUNT(*) FROM locations) AS total_locations,
    (SELECT COUNT(*) FROM sensors) AS total_sensors,
    (SELECT COUNT(measurement_id) FROM measurements) AS total_measurements,
    (SELECT COUNT(*) FROM parameters) AS total_parameters;
"""

df = pd.read_sql(query, engine)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total Locations",
    f"{df.iloc[0, 0]:,}",
    border=True
)

col2.metric(
    "Total Sensors",
    f"{df.iloc[0, 1]:,}",
    border=True
)

col3.metric(
    "Total Measurements",
    f"{df.iloc[0, 2]:,}",
    border=True
)

col4.metric(
    "Parameters",
    f"{df.iloc[0, 3]:,}",
    border=True
)


st.divider()


# --------------------------------------------------
# POLLUTANT LIST
# --------------------------------------------------

pollutant_list = [
    "pm1",
    "pm25",
    "pm10",
    "no",
    "no2",
    "nox",
    "o3",
    "co",
    "so2"
]


# --------------------------------------------------
# MONTHLY POLLUTION TREND
# --------------------------------------------------

st.subheader("Monthly Pollution Trend — 2025")

select_pollutant = st.selectbox(
    "Select pollutant",
    pollutant_list,
    key="monthly_pollutant"
)


def pollutant_trend(pollutant):

    query = text("""
        SELECT
            DATE_TRUNC('month', cp.datetime) AS month,
            ROUND(AVG(cp.value), 2) AS avg_value
        FROM clean_pollutants cp
        JOIN parameters p USING(parameter_id)
        WHERE EXTRACT(YEAR FROM cp.datetime) = 2025
          AND p.parameter_name = :pollutant_name
        GROUP BY month
        ORDER BY month;
    """)

    df = pd.read_sql(
        query,
        engine,
        params={"pollutant_name": pollutant}
    )

    st.line_chart(
        df,
        x="month",
        y="avg_value"
    )


pollutant_trend(select_pollutant)


st.divider()


# --------------------------------------------------
# LOCATION + PARAMETER COMPARISON
# --------------------------------------------------

col1, col2 = st.columns(2)


# --------------------------------------------------
# TOP 10 POLLUTED LOCATIONS
# --------------------------------------------------

with col1:

    st.subheader("Top 10 Polluted Locations")

    select_pollutant1 = st.selectbox(
        "Select pollutant",
        pollutant_list,
        key="location_pollutant"
    )


    def pollution_bar_chart(pollutant):

        query = text("""
            SELECT
                l.location_name,
                ROUND(AVG(cp.value), 2) AS avg_pollution
            FROM locations l
            JOIN sensors s USING(location_id)
            JOIN clean_pollutants cp USING(sensor_id)
            JOIN parameters p USING(parameter_id)
            WHERE p.parameter_name = :pollutant_name
            GROUP BY l.location_id, l.location_name
            ORDER BY avg_pollution DESC
            LIMIT 10;
        """)

        df = pd.read_sql(
            query,
            engine,
            params={"pollutant_name": pollutant}
        )

        st.bar_chart(
            df,
            x="location_name",
            y="avg_pollution"
        )

        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True
        )


    pollution_bar_chart(select_pollutant1)


# --------------------------------------------------
# OVERALL POLLUTANT COMPARISON
# --------------------------------------------------

with col2:

    st.subheader("Average Pollution by Parameter")

    query1 = text("""
        SELECT
            p.parameter_name,
            ROUND(AVG(cp.value), 2) AS avg_pollution
        FROM clean_pollutants cp
        JOIN parameters p USING(parameter_id)
        GROUP BY p.parameter_name
        ORDER BY avg_pollution DESC;
    """)

    df = pd.read_sql(query1, engine)

    st.bar_chart(
        df,
        x="parameter_name",
        y="avg_pollution"
    )

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True
    )


st.divider()


# --------------------------------------------------
# SEASONAL POLLUTION
# --------------------------------------------------

st.subheader("Seasonal Pollution — 2025–2026")

select_pollutant2 = st.selectbox(
    "Select pollutant",
    pollutant_list,
    key="seasonal_pollutant"
)


def seasonal_pollution(pollutant):

    query = text("""
        SELECT
            CASE
                WHEN EXTRACT(MONTH FROM cp.datetime)
                     IN (12, 1, 2, 3)
                    THEN 'Winter'

                WHEN EXTRACT(MONTH FROM cp.datetime)
                     IN (4, 5, 6, 7)
                    THEN 'Summer'

                ELSE 'Monsoon'
            END AS season,

            ROUND(AVG(cp.value)::numeric, 2) AS avg_value

        FROM clean_pollutants cp

        JOIN parameters p USING(parameter_id)

        WHERE cp.datetime >= '2025-01-01'
          AND cp.datetime < '2027-01-01'
          AND p.parameter_name = :pollutant_name

        GROUP BY season

        ORDER BY avg_value DESC;
    """)

    df = pd.read_sql(
        query,
        engine,
        params={"pollutant_name": pollutant}
    )

    st.bar_chart(
        df,
        x="season",
        y="avg_value"
    )

    st.dataframe(
        df,
        hide_index=True,
        use_container_width=True
    )


seasonal_pollution(select_pollutant2)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Air Quality Data Engineering Project | "
    "OpenAQ → Python → PostgreSQL → SQL → Streamlit"
)