import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace(
        'postgres://', 'postgresql://'
    ) or 'sqlite:///' + os.path.join(basedir, 'instance', 'eco_city.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(basedir, 'staticCSS', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    MAP_CENTER = [51.527623, 81.217673]
    MAP_ZOOM = 14
    MAP_TILES = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'

    DEBUG = False
