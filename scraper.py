import requests
import re
import json
import datetime
import argparse


def user_input():
    parser = argparse.ArgumentParser()
    parser.add_argument('origin', type=str, help='Start of route')
    parser.add_argument('destination', type=str, help='End for route')
    parser.add_argument('date', type=str, help='Date of departure')

    args = parser.parse_args()

    return get_response(args.origin, args.destination, args.date)


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
    location_list = create_location_list()
    source = city_to_id(source, location_list)
    destination = city_to_id(destination, location_list)
    #date = datetime.datetime.fromisoformat(date)

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
    print(response)
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


if __name__ == '__main__':
    routes = user_input()

    json_return = json.dumps(routes, indent=2)
    print(json_return)
