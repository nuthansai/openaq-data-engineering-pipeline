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



CREATE TABLE measurements (
	measurement_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	sensor_id INT REFERENCES sensors(sensor_id),
	parameter_id INT REFERENCES parameters(parameter_id),
	datetime TIMESTAMP NOT NULL,
	value FLOAT,

	CONSTRAINT uq_sensor_param_datetime UNIQUE (sensor_id, parameter_id, datetime)
);

