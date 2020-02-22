"""
This module contains functions that query external APIs
"""
import requests

from calories.main import cfg, logger


def calories_from_nutritionix(meal):
    """
    Query Nutritionix API to get the calories information of a meal
    :param meal: Name of the meal
    :type meal: str
    :return: The calories of the specified meal
    :rtype: int
    """
    auth = {"appId": cfg.NTX_APP_ID, "appKey": cfg.NTX_API_KEY}
    try:
        food_info = requests.get('/'.join([cfg.NTX_BASE_URL, 'search', meal]), params={**auth, 'results': '0:1'}).json()
    except (requests.RequestException, ValueError) as e:
        logger.warning(f"Exception happened while trying to get calories for '{meal}': {e} ")
        return 0

    if not food_info.get('total_hits', None):
        return 0
    try:
        meal_id = food_info['hits'][0]['fields']['item_id']
    except LookupError as e:
        logger.warning(f"Exception happened while trying to get calories for '{meal}': {e} ")
        return 0

    try:
        food_info = requests.get('/'.join([cfg.NTX_BASE_URL, 'item']), params={**auth, 'id': meal_id}).json()
    except (requests.RequestException, ValueError) as e:
        logger.warning(f"Exception happened while trying to get calories for '{meal}': {e} ")
        return 0

    logger.info(f"Successfully read calories from Nutrionix API for meal: '{meal}'")
    return food_info.get('nf_calories', 0)
