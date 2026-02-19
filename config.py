import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # В продакшене SECRET_KEY должен быть установлен через переменные окружения
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'

    # Используем PostgreSQL на Render (будет автоматически настроен)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://') or \
                              'sqlite:///' + os.path.join(basedir, 'instance', 'eco_city.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки для продакшена
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    # Настройки карты для Рубцовска
    MAP_CENTER = [51.527623, 81.217673]
    MAP_ZOOM = 14
    MAP_TILES = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

    # Отключаем режим отладки
    DEBUG = False