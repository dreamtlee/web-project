
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fitbot-v2-ultra-secret-key-999'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'fitbot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    YANDEX_GEO_API_KEY = '8013b162-6b42-4997-9691-77b7074026e0'
    YANDEX_WEATHER_API_KEY = 'fa0f11a5-fd86-48c2-b07f-ef6e45a933a8'
