import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'eco-city-rubtsovsk-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'instance', 'eco_city.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'obj', 'fbx', 'glb'}

    MAP_CENTER = [51.527623, 81.217673]
    MAP_ZOOM = 14

    MAP_TILES = 'https://core-renderer-tiles.maps.yandex.net/tiles?l=map&v=21.06.04-0-b210519094530&x={x}&y={y}&z={z}'
    MAP_ATTRIBUTION = '© <a href="https://yandex.ru/maps/">Яндекс.Карты</a>'
    YANDEX_MAP_API_KEY = '3213fdd7-a67f-47e0-abbc-7847e583f9b2'
