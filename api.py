from typing import Optional
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from scraper import RegioParser

app = FastAPI()


@app.get("/search/")
async def regio_paths(source: str, destination: str, departure_date: str, passengers: Optional[int] = None, to_date: Optional[str] = None):
    print(to_date)
    parser_data = RegioParser(
        source, destination, departure_date, passengers, to_date)
    return parser_data.all_routes
