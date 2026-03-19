import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'

    database_url = os.environ.get('DATABASE_URL', '')
    if database_url:
        # Заменяем postgres:// на postgresql:// если нужно
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
        # Вставляем +pg8000 после postgresql
        if database_url.startswith('postgresql://'):
            database_url = 'postgresql+pg8000://' + database_url[len('postgresql://'):]
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Локально используем SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'eco_city.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, 'staticCSS', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    MAP_CENTER = [51.527623, 81.217673]
    MAP_ZOOM = 14
    MAP_TILES = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

    DEBUG = False
