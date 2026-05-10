import requests
from config import Config

def get_weather(city="Москва"):
    try:
        geo_url = "https://geocode-maps.yandex.ru/1.x/"
        geo_params = {
            "apikey": Config.YANDEX_GEO_API_KEY,
            "geocode": city,
            "format": "json"
        }
        geo_data = requests.get(geo_url, params=geo_params).json()
        pos = geo_data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        lon, lat = pos.split()

        weather_url = "https://api.weather.yandex.ru/v2/informers"
        headers = {'X-Yandex-API-Key': Config.YANDEX_WEATHER_API_KEY}
        w_params = {'lat': lat, 'lon': lon, 'lang': 'ru_RU'}
        
        res = requests.get(weather_url, params=w_params, headers=headers).json()
        temp = res['fact']['temp']
        
        conditions = {
            'clear': 'ясно', 'partly-cloudy': 'малооблачно', 'cloudy': 'облачно',
            'overcast': 'пасмурно', 'drizzle': 'морось', 'light-rain': 'небольшой дождь',
            'rain': 'дождь', 'heavy-rain': 'сильный дождь', 'snow': 'снег'
        }
        cond = conditions.get(res['fact']['condition'], res['fact']['condition'])

        return f"В городе {city} сейчас {temp}°C, {cond}. Отличное время для тренировки!"
    except Exception:
        return "Не удалось получить данные о погоде. Но пробежка всё равно пойдет на пользу!"
