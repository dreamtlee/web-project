import requests
from config import Config

def get_weather(city):
    try:
        geocode_url = "http://geocode-maps.yandex.ru/1.x/"
        geocode_params = {
            "apikey": Config.YANDEX_GEO_API_KEY,
            "geocode": city,
            "format": "json"
        }
        geo_data = requests.get(geocode_url, params=geocode_params).json()
        coordinates = geo_data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
        lon, lat = coordinates.split()

        weather_url = "https://api.weather.yandex.ru/v2/informers"
        weather_headers = {"X-Yandex-API-Key": Config.YANDEX_WEATHER_API_KEY}
        weather_params = {"lat": lat, "lon": lon, "lang": "ru_RU"}
        
        weather_data = requests.get(weather_url, params=weather_params, headers=weather_headers).json()
        temperature = weather_data['fact']['temp']
        condition = weather_data['fact']['condition']
        
        conditions_map = {
            'clear': 'ясно', 'partly-cloudy': 'малооблачно', 'cloudy': 'облачно',
            'overcast': 'пасмурно', 'drizzle': 'морось', 'light-rain': 'небольшой дождь',
            'rain': 'дождь', 'moderate-rain': 'умеренно сильный дождь', 'heavy-rain': 'сильный дождь'
        }
        readable_cond = conditions_map.get(condition, condition)
        
        return f"В городе {city} сейчас {temperature}°C, {readable_cond}. Прекрасные условия для достижения новых рекордов!"
    except Exception as e:
        return "Сервис погоды временно недоступен, но это не повод пропускать тренировку!"
