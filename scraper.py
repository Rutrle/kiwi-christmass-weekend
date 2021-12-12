import requests
import re
import json
import argparse
from slugify import slugify
from redis import Redis
import datetime
from database_handler import database_connection, create_journey, get_journeys


def user_input():
    parser = argparse.ArgumentParser()
    parser.add_argument('origin', type=str, help='Start of route')
    parser.add_argument('destination', type=str, help='End for route')
    parser.add_argument('date', type=str, help='Date of departure')

    args = parser.parse_args()

    user_input = {
        'origin': args.origin,
        'destination': args.destination,
        'date': args.date
    }
    return user_input


class RegioParser:
    def __init__(self, user_origin, user_destination, user_date, passengers=None, date_to=None):
        print(date_to)
        if date_to == None:
            date_to = user_date

        self.user_origin = user_origin
        self.user_destination = user_destination
        self.user_date = user_date
        self.passengers = passengers

        self.date_to = date_to
        self.all_routes = []

        while self.user_date <= self.date_to:

            self.redis = self.redis_interface()

            self.uncleaned_routes = self.routes_switch(
                self.user_origin, self.user_destination, self.user_date)

            if self.passengers is not None:
                self.routes = self.check_enough_seats(
                    self.uncleaned_routes, self.passengers)
            else:
                self.routes = self.uncleaned_routes

            self.user_date += datetime.timedelta(days=1)
            self.all_routes.append(self.routes)

    def check_enough_seats(self, routes, passengers):
        new_routes = []
        for route in routes:
            if route['free_seats'] >= passengers:
                new_routes.append(route)
        return new_routes

    def routes_switch(self, source, destination, date):
        cache_value = self.redis_get_journey(
            source, destination, date)

        if cache_value is not None:
            print('cache_value')
            return cache_value
        else:
            print('NOT cache')
            routes = self.get_response(
                source, destination, self.user_date)

            self.redis_save_journey(source, destination, date, routes)
            self.postgres_save_journey(routes)
            return routes

    def redis_interface(self):
        redis_instance = "redis.pythonweekend.skypicker.com"
        redis = Redis(host=redis_instance,  port=6379,
                      db=0, decode_responses=True)

        return redis

    def city_to_id(self, city):
        if self.redis_get_locations(city) != None:
            print(city, 'from cache')
            return self.redis_get_locations(city)

        location_list = self.create_location_list()
        for entry in location_list:
            if city in entry['names']:
                self.redis_save_location(city, entry['id'])
                return entry['id']

    def create_location_list(self):
        address = 'https://brn-ybus-pubapi.sa.cz/restapi/consts/locations'
        response = requests.get(address).json()
        location_list = []
        for country in response:
            for city in country['cities']:
                name_list = city['aliases']
                name_list.append(city['name'])
                city_log = {
                    "id": city['id'],
                    "names": name_list
                }
                location_list.append(city_log)

        return location_list

    def get_response(self, source, destination, date: datetime.datetime):
        source = self.city_to_id(source)
        destination = self.city_to_id(destination)

        host = 'https://brn-ybus-pubapi.sa.cz/restapi/routes/search/simple'
        params = {
            'tariffs': 'REGULAR',
            'toLocationType': 'CITY',
            'toLocationId': destination,
            'fromLocationType': 'CITY',
            'fromLocationId': source,
            'departureDate': date.isoformat(),
            "locale": "cs"
        }

        response = requests.get(host,
                                params=params)
        response = response.json()
        response_routes = response['routes']
        cleaned_routes = []

        for route in response_routes:
            current_route = {
                "departure_datetime": route["departureTime"],
                "arrival_datetime": route["arrivalTime"],
                "source": source,
                "destination": destination,
                "fare": {
                    "amount": float(route['priceFrom']),
                    "currency": "EUR"
                },
                "type": route['vehicleTypes'],
                "source_id": route['departureStationId'],
                "destination_id": route['departureStationId'],
                "free_seats": route['freeSeatsCount'],
                "carrier": "REGIOJET"
            }

            cleaned_routes.append(current_route)

        return cleaned_routes

    def redis_save_journey(self, source, destination, date, value):
        source = slugify(source, separator='_')
        destination = slugify(destination, separator='_')
        key = f"rutrle:journey:{source}_{destination}_{date}"

        self.redis.set(key, json.dumps(value))

    def redis_get_journey(self, source, destination, date):
        source = slugify(source, separator='_')
        destination = slugify(destination, separator='_')
        key = f"rutrle:journey:{source}_{destination}_{date}"
        maybe_value = self.redis.get(key)
        if maybe_value is None:
            return None
        return json.loads(maybe_value)

    def redis_save_location(self, location, id):
        location = slugify(location, separator='_')
        key = f"rutrle:location:{location}"
        self.redis.set(key, json.dumps(id))

    def redis_get_locations(self, location):
        location = slugify(location, separator='_')
        key = f"rutrle:location:{location}"
        maybe_value = self.redis.get(key)

        if maybe_value is None:
            return None
        return json.loads(maybe_value)

    def postgres_save_journey(self, routes):
        for route in routes:
            data = {
                "source": route['source'],
                "destination": route['destination'],
                "departure_datetime": datetime.datetime.fromisoformat(route['departure_datetime']),
                "arrival_datetime": datetime.datetime.fromisoformat(route['arrival_datetime']),
                "carrier": route["carrier"],
                "vehicle_type": route['type'][0].lower(),
                "price": route["fare"]["amount"],
                "currency": "EUR"
            }
            with database_connection() as conn:
                create_journey(conn, data)


if __name__ == '__main__':
    users_input = user_input()
    parser = RegioParser(
        users_input['origin'], users_input['destination'], users_input['date'])
