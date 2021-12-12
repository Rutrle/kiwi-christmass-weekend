from datetime import datetime
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection, Row
from typing import Optional, List
from sqlalchemy import select, Column, Integer, MetaData, Numeric, Sequence, String, Table, TEXT, UniqueConstraint, create_engine, alias, and_

from sqlalchemy.dialects.postgresql import ENUM, TIMESTAMP
from contextlib import contextmanager

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

DATABASE_URL = "postgresql://pythonweekend:9SRK7eJG6T8rirWW@sql.pythonweekend.skypicker.com/pythonweekend"
engine = create_engine(
    DATABASE_URL,
    pool_size=1,
    max_overflow=0,
    echo=True,
)


def create_journey(connection: Connection, journey) -> Optional[Row]:
    query = insert(Journeys).values(
        **journey).returning("*").on_conflict_do_nothing()  # rozbalí dict do jednotlivých parametrů
    executed_query = connection.execute(query)
    return executed_query.one_or_none()


@contextmanager
def database_connection():
    with engine.connect() as connection:
        yield connection


def get_journeys(connection: Connection, destination: str) -> List[Row]:
    query = select(Journeys).where(Journeys.c.destination == destination)
    rows = connection.execute(query).all()
    return rows


class JoinTable():
    def __init__(self, source, destination, departure: datetime):
        self.join_table_results = self.join_table(
            source, destination, departure)

    def join_table(self, source: str, destination: str, departure: datetime):
        aJourneys = alias(Journeys)
        query = select([Journeys, aJourneys]).join(
            aJourneys, Journeys.c.destination == aJourneys.c.source
        ).where(and_(
            Journeys.c.source == source, aJourneys.c.destination == destination,
            Journeys.c.departure_datetime >= departure
        )
        )
        with database_connection() as conn:
            results = conn.execute(query).fetchall()

            return results
        ''' 
        for combination in results:
            yield {
                "source": combination["source"],
                "stopover": combination["destination"],
                "destination": combination["destination_1"],
                "departure_datetime": combination["departure_datetime"],
                "arrival_datetime": combination["arrival_datetime_1"]
            }
        '''


if __name__ == '__main__':
    join_table = JoinTable('brno', 'kosice', datetime.today())
    g = join_table.join_table_results

    print("res")
    print(list(g))
    print('_'*40 + 'results')

    for result in join_table.join_table_results:
        print(result)
