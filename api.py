from datetime import date, datetime
from typing import Optional
from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from scraper import RegioParser
from fastapi.middleware.cors import CORSMiddleware
from database_handler import JoinTable
app = FastAPI()
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://192.168.51.38:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/search")
async def regio_paths(origin: str, destination: str, departure: datetime, passengers: Optional[int] = None, to_date: Optional[datetime] = None):
    parser_data = RegioParser(
        origin, destination, departure, passengers, to_date)
    return parser_data.all_routes[0]

''' 
@app.get("/search/database")
async def regio_paths(origin: str, destination: str, departure: datetime, passengers: Optional[int] = None, to_date: Optional[datetime] = None):
    parser_data = RegioParser(
        origin, destination, departure, passengers, to_date)
    return parser_data.all_routes[0]
'''
