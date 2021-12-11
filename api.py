from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from scraper import RegioParser

app = FastAPI()


@app.get("/search/")
async def regio_paths(source: str, destination: str, departure_date: str):
    parser_data = RegioParser(source, destination, departure_date)
    return parser_data.routes
