import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'fitbot-secret-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'fitbot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    YANDEX_GEO_API_KEY = '8013b162-6b42-4997-9691-77b7074026e0'
    YANDEX_WEATHER_API_KEY = 'ВСТАВЬ КЛЮЧ ПОГОДЫ!'
    
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
