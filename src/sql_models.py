from sqlalchemy import Table, Column, Integer, DateTime, Numeric, MetaData, UniqueConstraint, ForeignKey, Text

metadata = MetaData()

measurements = Table(
    "measurements",
    metadata,
    Column("measurement_id", Integer, primary_key=True),
    Column("sensor_id", Integer, ForeignKey("sensors.sensor_id")),
    Column("parameter_id", Integer, ForeignKey("parameters.parameter_id")),
    Column("datetime", DateTime),
    Column("value", Numeric),
    UniqueConstraint("sensor_id", "parameter_id", "datetime", name="unq_measurements")
)

locations = Table(
    "locations",
    metadata,
    Column("location_id", Integer, primary_key=True),
    Column("location_name", Text)
)

parameters = Table(
    "parameters",
    metadata,
    Column("parameter_id", Integer, primary_key=True),
    Column("parameter_name", Text),
    Column("parameter_unit", Text)
)

sensors = Table(
    "sensors",
    metadata,
    Column("sensor_id", Integer, primary_key=True),
    Column("location_id", Integer, ForeignKey("locations.location_id"))
)