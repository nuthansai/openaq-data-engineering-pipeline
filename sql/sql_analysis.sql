SELECT * FROM locations LIMIT 10;

SELECT * FROM measurements LIMIT 5;

SELECT DISTINCT parameter_name FROM parameters;

SELECT * FROM sensors LIMIT 5;

SELECT * FROM clean_pollutants LIMIT 5;

SELECT * FROM clean_meteorological LIMIT 5;

-- Identified -ve values in the dataset using below query which is a data quality issue

SELECT parameter_name, parameter_unit, COUNT(*) as measurement_count, 
ROUND(AVG(value)::numeric, 2) as avg_value,
ROUND(MIN(value)::numeric, 2) as min_value,
ROUND(MAX(value)::numeric, 2) as max_value
FROM measurements m
JOIN parameters p ON m.parameter_id = p.parameter_id
GROUP BY parameter_name, parameter_unit
ORDER BY measurement_count DESC;

-- Creating  VIEWs to filter the -ve values and separating pollutant data and meteorological data

CREATE VIEW clean_pollutants AS
SELECT m.* 
FROM measurements m
JOIN parameters p USING(parameter_id)
WHERE p.parameter_name IN (
    'pm1',
    'pm25',
    'pm10',
    'no',
    'no2',
    'nox',
    'o3',
    'co',
    'so2'
) AND value >= 0;

CREATE VIEW clean_meteorological AS
SELECT m.*
FROM measurements m
JOIN parameters p USING (parameter_id)
WHERE p.parameter_name IN (
    'temperature',
    'relativehumidity',
    'wind_speed',
    'wind_direction'
)
AND m.value >= 0;

-- Top 10 locations have the worst NO2 levels on average

SELECT 
	l.location_name,
	ROUND(AVG(m.value),2) AS avg_no2
FROM locations l
JOIN sensors s USING(location_id)
JOIN clean_pollutants m USING(sensor_id)
JOIN parameters p USING(parameter_id)
WHERE p.parameter_name = 'no2'
GROUP BY l.location_id, l.location_name
ORDER BY avg_no2 DESC
LIMIT 10;

-- Top 10 locations that have the cleanest air

SELECT 
	l.location_name,
	ROUND(AVG(m.value),2) AS avg_value
FROM locations l
JOIN sensors s USING(location_id)
JOIN clean_pollutants m USING(sensor_id)
JOIN parameters p USING(parameter_id)
GROUP BY l.location_id, l.location_name
ORDER BY avg_value
LIMIT 10;

-- location that has the most sensor coverage

SELECT 
	l.location_name,
	COUNT(s.sensor_id) as sensor_cnt
FROM locations l
JOIN sensors s USING(location_id)
GROUP BY l.location_id, l.location_name
ORDER BY sensor_cnt DESC;

-- location showed the biggest improvement between Febrauary and December 2025

WITH cte1 AS (
	SELECT
		l.location_name,
		ROUND(AVG(m.value),2) AS avg_feb_no2
	FROM locations l
	JOIN sensors s USING(location_id)
	JOIN clean_pollutants m USING(sensor_id) 
	JOIN parameters p USING(parameter_id)
	WHERE p.parameter_name = 'no2' AND m.datetime >= '2025-02-01' AND m.datetime <= '2025-02-28'
	GROUP BY l.location_id, l.location_name
),

cte2 AS (
	SELECT
		l.location_name,
		ROUND(AVG(m.value),2) AS avg_dec_no2
	FROM locations l
	JOIN sensors s USING(location_id)
	JOIN clean_pollutants m USING(sensor_id) 
	JOIN parameters p USING(parameter_id)
	WHERE p.parameter_name = 'no2' AND m.datetime >= '2025-12-01' AND m.datetime < '2026-01-01'
	GROUP BY l.location_id, l.location_name
)

SELECT
	location_name,
	c1.avg_feb_no2,
	c2.avg_dec_no2,
	(c1.avg_feb_no2 - c2.avg_dec_no2) AS improvement
FROM cte1 c1
JOIN cte2 c2 USING(location_name)
WHERE (c1.avg_feb_no2 - c2.avg_dec_no2) > 0 
ORDER BY improvement DESC;

-- Which location has the highest average temperature in 2025

SELECT 
	l.location_name AS city,
	ROUND(AVG(cm.value),2) AS avg_temp_value
FROM locations l
JOIN sensors s USING(location_id)
JOIN clean_meteorological cm USING (sensor_id)
JOIN parameters p USING(parameter_id)
WHERE cm.datetime >= '01-01-2025' AND cm.datetime < '01-01-2026' AND p.parameter_name = 'temperature'
GROUP BY l.location_id, l.location_name
ORDER BY avg_temp_value DESC
LIMIT 1;



-- Which location has the most volatile pollution — highest day to day variation

WITH cte AS (SELECT 
	l.location_name,
	ABS(
		cp.value - LAG(cp.value) OVER (PARTITION BY l.location_name ORDER BY cp.datetime)
	) AS change
FROM locations l
JOIN sensors s USING(location_id)
JOIN clean_pollutants cp USING(sensor_id)
)

SELECT 
	location_name,
	ROUND(AVG(change),2) AS avg_variation
FROM cte
GROUP BY location_name
ORDER BY 2 DESC
LIMIT 1;

-- Exploring the dataset again for the next analysis
SELECT l.location_name, s.sensor_id, p.parameter_name, m.value, m.datetime FROM locations l JOIN sensors s USING(location_id)
JOIN clean_pollutants m USING(sensor_id) JOIN parameters p USING(parameter_id) WHERE l.location_name = 'Jigani, Bengaluru - KSPCB' AND m.value > 100;

--  parameter exceeds its safety threshold most frequently across all locations

-- Parameter	Safe Limit	Unit
-- PM2.5			15		µg/m³
-- PM10				45		µg/m³
-- NO2				25		ppb
-- SO2				40		ppb
-- O3				100		µg/m³
-- CO				4000	ppb

SELECT 
	p.parameter_name,
	COUNT(
		CASE
			WHEN parameter_name = 'pm25' AND cp.value > 15 THEN 1
			WHEN parameter_name = 'pm10' AND cp.value > 45 THEN 1
			WHEN parameter_name = 'no2' AND cp.value > 25 THEN 1
			WHEN parameter_name = 'SO2' AND cp.value > 40 THEN 1
			WHEN parameter_name = 'o3' AND cp.value > 100 THEN 1
			WHEN parameter_name = 'co' AND cp.value > 4000 THEN 1
		END
			) AS exceeded_count
FROM clean_pollutants cp
JOIN parameters p USING (parameter_id)
GROUP BY p.parameter_name 
ORDER BY exceeded_count desc
LIMIT 1;

-- How does average temperature trend month by month across all locations

SELECT 
	TO_CHAR(cm.datetime,'Mon YYYY') AS month,
	ROUND(AVG(cm.value),2) AS avg_temp_value
FROM locations l
JOIN sensors s USING(location_id)
JOIN clean_meteorological cm USING (sensor_id)
JOIN parameters p USING(parameter_id)
WHERE p.parameter_name = 'temperature'
GROUP BY month;

-- Which location has the most extreme temperature variation day to day

WITH cte AS (
SELECT 
	l.location_id,
	l.location_name AS city,
	ABS(
		cm.value - LAG(cm.value) OVER (PARTITION BY l.location_name ORDER BY cm.datetime)
	) AS temp_change
FROM locations l
JOIN sensors s USING(location_id)
JOIN clean_meteorological cm USING (sensor_id)
JOIN parameters p USING(parameter_id)
WHERE cm.datetime >= '01-01-2025' AND cm.datetime < '01-01-2026' AND p.parameter_name = 'temperature'
)

SELECT 
	city,
	ROUND(AVG(temp_change),2) AS temp_variation
FROM cte
GROUP BY location_id, city
ORDER BY temp_variation DESC
LIMIT 1;

--Which month in 2025 had the worst air quality nationally

WITH monthly_pollution AS (
    SELECT
        DATE_TRUNC('month', cp.datetime) AS month,
        AVG(cp.value) AS avg_pollution
    FROM clean_pollutants cp
    JOIN parameters p USING (parameter_id)
    WHERE p.parameter_name = 'pm25'
      AND cp.datetime >= '2025-01-01'
      AND cp.datetime < '2026-01-01'
    GROUP BY DATE_TRUNC('month', cp.datetime)
)

SELECT
    TO_CHAR(month, 'Mon YYYY') AS month,
    ROUND(avg_pollution, 2) AS avg_pollution
FROM monthly_pollution
ORDER BY avg_pollution DESC
LIMIT 1;


-- Are weekdays more polluted than weekends

SELECT 
	(CASE
		WHEN EXTRACT(DOW FROM cp.datetime) IN (0,6) THEN 'Weekend'
		ELSE 'Weekday'
	END) week_type,
	p.parameter_name,
	ROUND(AVG(cp.value),2) AS avg_value
FROM clean_pollutants cp
JOIN parameters p USING(parameter_id)
GROUP BY week_type, p.parameter_name
ORDER BY parameter_name;

--Which location has the highest average wind speed

SELECT 
	l.location_name AS city,
	ROUND(AVG(cm.value),2) AS avg_windspeed_value
FROM locations l
JOIN sensors s USING(location_id)
JOIN clean_meteorological cm USING (sensor_id)
JOIN parameters p USING(parameter_id)
WHERE p.parameter_name = 'wind_speed'
GROUP BY l.location_id, l.location_name
ORDER BY avg_windspeed_value DESC
LIMIT 1;

-- How does pollution trend from January to December 2025

SELECT 
	TO_CHAR(datetime, 'Mon YYYY') AS month,
	p.parameter_name,
	ROUND(AVG(cp.value),2) AS avg_value
FROM clean_pollutants cp
JOIN parameters p USING(parameter_id)
WHERE EXTRACT(YEAR FROM datetime) = 2025
GROUP BY month, p.parameter_name
ORDER BY parameter_name;

-- Do high wind speed cities have lower pollution levels — does wind clean the air

WITH avg_wind_speed AS (
    SELECT
        l.location_id,
        l.location_name,
        ROUND(AVG(cm.value), 2) AS avg_wind_speed
    FROM locations l
    JOIN sensors s USING (location_id)
    JOIN clean_meteorological cm USING (sensor_id)
    JOIN parameters p USING (parameter_id)
    WHERE p.parameter_name = 'wind_speed'
    GROUP BY l.location_id, l.location_name
),

avg_pm25 AS (
    SELECT
        l.location_id,
        l.location_name,
        ROUND(AVG(cp.value), 2) AS avg_pm25
    FROM locations l
    JOIN sensors s USING (location_id)
    JOIN clean_pollutants cp USING (sensor_id)
    JOIN parameters p USING (parameter_id)
    WHERE p.parameter_name = 'pm25'
    GROUP BY l.location_id, l.location_name
)

SELECT
    aw.location_name,
    aw.avg_wind_speed,
    ap.avg_pm25
FROM avg_wind_speed aw
JOIN avg_pm25 ap USING (location_id)
ORDER BY aw.avg_wind_speed DESC;

-- Which season has the highest average pollution? (2025–2026)
-- Assumption:
-- Winter  = Dec, Jan, Feb, Mar
-- Summer  = Apr, May, Jun, Jul
-- Monsoon = Aug, Sep, Oct, Nov

SELECT
    CASE
        WHEN EXTRACT(MONTH FROM cp.datetime) IN (12, 1, 2, 3) THEN 'Winter'
        WHEN EXTRACT(MONTH FROM cp.datetime) IN (4, 5, 6, 7) THEN 'Summer'
        ELSE 'Monsoon'
    END AS season,
    p.parameter_name,
    ROUND(AVG(cp.value)::numeric, 2) AS avg_value
FROM clean_pollutants cp
JOIN parameters p USING (parameter_id)
WHERE cp.datetime >= '2025-01-01'
  AND cp.datetime < '2027-01-01'
GROUP BY
    season,
    p.parameter_name
ORDER BY
    p.parameter_name,
    avg_value DESC;

-- Which location has the highest average humidity

SELECT 
	l.location_name AS city,
	ROUND(AVG(cm.value),2) AS avg_humidity_value
FROM locations l
JOIN sensors s USING(location_id)
JOIN clean_meteorological cm USING (sensor_id)
JOIN parameters p USING(parameter_id)
WHERE p.parameter_name = 'relativehumidity'
GROUP BY l.location_id, l.location_name
ORDER BY avg_humidity_value DESC
LIMIT 1;

-- Is there a correlation between high humidity locations and high pollution locations

WITH avg_humidity AS (
    SELECT
        l.location_id,
        l.location_name,
        ROUND(AVG(cm.value), 2) AS avg_humidity
    FROM locations l
    JOIN sensors s USING (location_id)
    JOIN clean_meteorological cm USING (sensor_id)
    JOIN parameters p USING (parameter_id)
    WHERE p.parameter_name = 'relativehumidity'
    GROUP BY l.location_id, l.location_name
),

avg_pm25 AS (
    SELECT
        l.location_id,
        l.location_name,
        ROUND(AVG(cp.value), 2) AS avg_pm25
    FROM locations l
    JOIN sensors s USING (location_id)
    JOIN clean_pollutants cp USING (sensor_id)
    JOIN parameters p USING (parameter_id)
    WHERE p.parameter_name = 'pm25'
    GROUP BY l.location_id, l.location_name
)

SELECT
    ah.location_name,
    ah.avg_humidity,
    ap.avg_pm25
FROM avg_humidity ah
JOIN avg_pm25 ap USING (location_id)
ORDER BY ah.avg_humidity DESC;

-- Which city has the most consistent wind direction
-- Assumption:
-- Wind direction consistency is measured using standard deviation.
-- Lower standard deviation indicates more consistent wind direction.

SELECT
    l.location_name,
    ROUND(AVG(cm.value), 2) AS avg_wind_direction,
    ROUND(STDDEV(cm.value), 2) AS wind_direction_stddev
FROM locations l
JOIN sensors s USING (location_id)
JOIN clean_meteorological cm USING (sensor_id)
JOIN parameters p USING (parameter_id)
WHERE p.parameter_name = 'wind_direction'
GROUP BY
    l.location_id,
    l.location_name
ORDER BY
    wind_direction_stddev ASC;

--Which parameter has the most complete data coverage

SELECT
    p.parameter_name,
    COUNT(*) AS measurement_count
FROM clean_pollutants cp
JOIN parameters p USING (parameter_id)
GROUP BY
    p.parameter_id,
    p.parameter_name
ORDER BY measurement_count DESC;