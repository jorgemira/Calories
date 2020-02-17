from requests import request

BASE_URL = "https://api.nutritionix.com/v1_1/"
APP_ID = "29787544"
API_KEY = "e0ecc4ea5307e6392caba2dd9023085f"


def calories_from_nutritionix(meal):
    auth = {"appId": APP_ID, "appKey": API_KEY}
    try:
        food_info = request('get', '/'.join([BASE_URL, 'search', meal]), params={**auth, 'results': '0:1'}).json()
    except (ConnectionError, ValueError):
        # TODO log it
        return 0

    if not food_info['total_hits']:
        print('Food not found')  # Change to logger
        return 0

    meal_id = food_info['hits'][0]['fields']['item_id']
    try:
        food_info = request('get', '/'.join([BASE_URL, 'item']), params={**auth, 'id': meal_id}).json()
    except (ConnectionError, ValueError) as e:
        # TODO log it
        return 0
    return food_info['nf_calories']
