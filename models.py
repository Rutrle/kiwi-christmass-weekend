from sqlalchemy import Column, Integer, MetaData, Numeric, Sequence, String, Table, TEXT, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, TIMESTAMP

metadata = MetaData()

Journeys = Table(
    "journeys",
    metadata,
    Column("id", Integer, Sequence("journeys_seq"), primary_key=True),
    Column("source", TEXT, index=True, nullable=False),
    Column("destination", TEXT, index=True, nullable=False),
    Column("departure_datetime", TIMESTAMP, nullable=False),
    Column("arrival_datetime", TIMESTAMP, nullable=False),
    Column("carrier", TEXT, index=True, nullable=False),
    Column("vehicle_type", ENUM(
        "airplane", "bus", "train", name="vehicle_type")),
    Column("price", Numeric(20, 6), nullable=False),
    Column("currency", String(3), nullable=False),
    UniqueConstraint("source", "destination", "departure_datetime",
                     "arrival_datetime", "carrier", name="unique_journeys"),
)
