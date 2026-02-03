import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'eco-city-rubtsovsk-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'instance', 'eco_city.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Настройки загрузки файлов
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'obj', 'fbx', 'glb'}

    # Настройки карты для Рубцовска
    MAP_CENTER = [51.527623, 81.217673]  # Координаты Рубцовска
    MAP_ZOOM = 14
    MAP_TILES = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'