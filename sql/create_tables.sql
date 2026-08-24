CREATE TABLE locations (
	location_id INT PRIMARY KEY,
	location_name VARCHAR(50) 
);

CREATE TABLE parameters (
	parameter_id INT PRIMARY KEY,
	parameter_name VARCHAR(50),
	parameter_unit VARCHAR(25)
);

CREATE TABLE sensors (
	sensor_id INT PRIMARY KEY,
	location_id INT REFERENCES locations(location_id)
);

CREATE SEQUENCE measurement_seq
	START WITH 1
	INCREMENT BY 1
	NO MAXVALUE
	NO CYCLE;


CREATE TABLE measurements (
	measurement_id INT PRIMARY KEY 
		DEFAULT nextval('measurement_seq'),
	sensor_id INT REFERENCES sensors(sensor_id),
	parameter_id INT REFERENCES parameters(parameter_id),
	datetime TIMESTAMP,
	value NUMERIC 
);

