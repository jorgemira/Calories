import requests

from calories.main import cfg


def calories_from_nutritionix(meal):
    auth = {"appId": cfg.NTX_APP_ID, "appKey": cfg.NTX_API_KEY}
    try:
        food_info = requests.get('/'.join([cfg.NTX_BASE_URL, 'search', meal]), params={**auth, 'results': '0:1'}).json()
    except (requests.RequestException, ValueError):
        # TODO log it
        return 0

    if not food_info.get('total_hits', None):
        print('Food not found')  # TODO Change to logger
        return 0
    try:
        meal_id = food_info['hits'][0]['fields']['item_id']
    except LookupError:
        # TODO log it
        return 0

    try:
        food_info = requests.get('/'.join([cfg.NTX_BASE_URL, 'item']), params={**auth, 'id': meal_id}).json()
    except (requests.RequestException, ValueError):
        # TODO log it
        return 0

    return food_info.get('nf_calories', 0)
