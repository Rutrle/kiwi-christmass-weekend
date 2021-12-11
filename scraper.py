import requests
import re
import json
import datetime
import argparse
from slugify import slugify
from redis import Redis


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


def city_to_id(city, location_list):
    for entry in location_list:
        if city in entry['names']:
            return entry['id']


def create_location_list():
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


def get_response(source, destination, date='2021-12-12'):

    # date = datetime.datetime.fromisoformat(date)

    host = 'https://brn-ybus-pubapi.sa.cz/restapi/routes/search/simple'
    params = {
        'tariffs': 'REGULAR',
        'toLocationType': 'CITY',
        'toLocationId': destination,
        'fromLocationType': 'CITY',
        'fromLocationId': source,
        'departureDate': date,
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
                "amount": route['priceFrom'],
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


def redis_interface():

    redis_instance = "redis.pythonweekend.skypicker.com"

    redis = Redis(host=redis_instance,  port=6379,  db=0)

    return redis


def redis_save_journey(redis, source, destination, date, value):
    source = slugify(source, separator='_')
    destination = slugify(destination, separator='_')
    key = f"rutrle:journey:{source}_{destination}_{date}"

    redis.set(key, json.dumps(value))


def redis_get_journey(redis, source, destination, date):
    source = slugify(source, separator='_')
    destination = slugify(destination, separator='_')
    key = f"rutrle:journey:{source}_{destination}_{date}"
    maybe_value = redis.get(key)
    if maybe_value is None:
        return None
    return json.loads(maybe_value)


def redis_save_location(redis, location, id):
    location = slugify(location, separator='_')
    key = f"rutrle:location:{location}"
    redis.set(key, json.dumps(id))


def redis_get_locations(redis, location):
    location = slugify(location, separator='_')
    key = f"rutrle:location:{location}"
    maybe_value = redis.get(key)

    if maybe_value is None:
        return None
    return json.loads(maybe_value)


if __name__ == '__main__':
    user_input = user_input()

    location_list = create_location_list()
    source_id = city_to_id(user_input['origin'], location_list)
    destination_id = city_to_id(user_input['destination'], location_list)

    routes = get_response(source_id, destination_id, user_input['date'])

    json_return = json.dumps(routes, indent=2)
    # print(json_return)

    redis = redis_interface()
    redis_save_journey(
        redis, user_input['origin'], user_input['destination'], user_input['date'], json_return)

    redis_return = redis_get_journey(redis, user_input['origin'],
                                     user_input['destination'], user_input['date'])

    redis_save_location(redis, user_input['origin'], source_id)

    redis_location = redis_get_locations(redis, user_input['origin'])
    print(redis_return)
    print(redis_location)
