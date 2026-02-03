import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Создаём папки для файлов если они не существуют
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)

# Инициализируем базу данных SQLAlchemy
db = SQLAlchemy(app)

# Инициализируем менеджер авторизации Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'  # Страница для входа


# Определяем модель пользователя для базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный ID
    username = db.Column(db.String(80), unique=True, nullable=False)  # Логин
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email
    password_hash = db.Column(db.String(200), nullable=False)  # Хэш пароля
    city = db.Column(db.String(50), default='Рубцовск')  # Город пользователя
    is_admin = db.Column(db.Boolean, default=False)  # Права администратора
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата регистрации


# Определяем модель идеи/предложения
class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Уникальный ID идеи
    title = db.Column(db.String(200), nullable=False)  # Заголовок идеи
    description = db.Column(db.Text, nullable=False)  # Описание идеи
    category = db.Column(db.String(50), nullable=False)  # Категория (спорт, экология и т.д.)
    latitude = db.Column(db.Float, nullable=False)  # Широта на карте
    longitude = db.Column(db.Float, nullable=False)  # Долгота на карте
    status = db.Column(db.String(20), default='pending')  # Статус: pending, approved, rejected, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата создания
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ID автора
    votes_count = db.Column(db.Integer, default=0)  # Количество голосов

    # Связь с пользователем (автором)
    author = db.relationship('User', backref='ideas', lazy=True)


# Функция для загрузки пользователя (требуется для Flask-Login)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Главная страница - ОТОБРАЖАЕМ index.html, а не перенаправляем на карту
@app.route('/')
def index():
    # Загружаем последние идеи для отображения на главной
    recent_ideas = Idea.query.order_by(Idea.created_at.desc()).limit(3).all()
    total_ideas = Idea.query.count()
    total_users = User.query.count()

    return render_template('index.html',
                           recent_ideas=recent_ideas,
                           total_ideas=total_ideas,
                           total_users=total_users)


# Страница с интерактивной картой
@app.route('/map')
def map_view():
    # Список категорий для фильтрации на карте
    categories = ['спорт', 'культура', 'экология', 'озеленение', 'безопасность', 'другое']

    # Отправляем список категорий в шаблон для отображения фильтров
    return render_template('map.html',
                           categories=categories,
                           map_center=app.config['MAP_CENTER'],  # Центр карты (Рубцовск)
                           map_zoom=app.config['MAP_ZOOM'])  # Уровень приближения


# API для получения списка идей с фильтрацией
@app.route('/api/ideas', methods=['GET'])
def get_ideas():
    # Получаем параметры фильтрации из запроса
    category = request.args.get('category')  # Категория для фильтра
    status = request.args.get('status')  # Статус для фильтра

    # Начинаем запрос к базе данных
    query = Idea.query

    # Применяем фильтры если они указаны
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)

    # Получаем все отфильтрованные идеи
    ideas = query.all()

    # Формируем список для возврата в формате JSON
    result = []
    for idea in ideas:
        result.append({
            'id': idea.id,
            'title': idea.title,
            'description': idea.description,
            'category': idea.category,
            'latitude': idea.latitude,
            'longitude': idea.longitude,
            'status': idea.status,
            'votes_count': idea.votes_count,
            'author': idea.author.username,
            'created_at': idea.created_at.isoformat()
        })

    # Возвращаем результат в формате JSON
    return jsonify(result)


# API для создания новой идеи (только для авторизованных пользователей)
@app.route('/api/ideas', methods=['POST'])
@login_required  # Требуется авторизация
def create_idea():
    try:
        # Получаем данные из JSON запроса
        data = request.json

        # Создаём новую идею
        idea = Idea(
            title=data['title'],  # Заголовок
            description=data['description'],  # Описание
            category=data['category'],  # Категория
            latitude=data['latitude'],  # Широта
            longitude=data['longitude'],  # Долгота
            user_id=current_user.id  # ID текущего пользователя
        )

        # Добавляем идею в базу данных
        db.session.add(idea)
        db.session.commit()  # Сохраняем изменения

        # Возвращаем успешный ответ с ID созданной идеи
        return jsonify({'success': True, 'id': idea.id})
    except Exception as e:
        # Если произошла ошибка, возвращаем её описание
        return jsonify({'success': False, 'error': str(e)}), 400


# API для получения конкретной идеи по ID
@app.route('/api/ideas/<int:idea_id>', methods=['GET'])
def get_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    return jsonify({
        'id': idea.id,
        'title': idea.title,
        'description': idea.description,
        'category': idea.category,
        'latitude': idea.latitude,
        'longitude': idea.longitude,
        'status': idea.status,
        'votes_count': idea.votes_count,
        'author': idea.author.username,
        'created_at': idea.created_at.isoformat()
    })


# Страница регистрации нового пользователя
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Если запрос POST - обрабатываем форму регистрации
    if request.method == 'POST':
        # Получаем данные из формы
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        city = request.form.get('city', 'Рубцовск')  # По умолчанию Рубцовск

        # Проверяем обязательные поля
        if not username or not email or not password:
            flash('Заполните все обязательные поля')
            return redirect(url_for('register'))

        # Проверяем совпадение паролей
        if password != confirm_password:
            flash('Пароли не совпадают')
            return redirect(url_for('register'))

        # Проверяем минимальную длину пароля
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов')
            return redirect(url_for('register'))

        # Проверяем, не занят ли логин
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято')
            return redirect(url_for('register'))

        # Проверяем, не занят ли email
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован')
            return redirect(url_for('register'))

        # Создаём нового пользователя
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),  # Хэшируем пароль
            city=city
        )

        # Добавляем пользователя в базу данных
        db.session.add(user)
        db.session.commit()

        # Автоматически авторизуем пользователя после регистрации
        login_user(user)

        # Показываем сообщение об успехе
        flash(f'Добро пожаловать, {username}!', 'success')

        # Перенаправляем на главную страницу
        return redirect(url_for('index'))

    # Если запрос GET - показываем форму регистрации
    return render_template('auth/register.html')


# Страница входа в систему
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Если пользователь уже авторизован, перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Если запрос POST - обрабатываем форму входа
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Ищем пользователя в базе данных
        user = User.query.filter_by(username=username).first()

        # Проверяем пароль
        if user and check_password_hash(user.password_hash, password):
            # Авторизуем пользователя
            login_user(user)

            # Перенаправляем на запрошенную страницу или на главную
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            # Если данные неверные, показываем ошибку
            flash('Неверное имя пользователя или пароль')

    # Если запрос GET - показываем форму входа
    return render_template('auth/login.html')


# Выход из системы
@app.route('/logout')
@login_required  # Только для авторизованных пользователей
def logout():
    logout_user()  # Завершаем сессию пользователя
    return redirect(url_for('index'))  # Перенаправляем на главную


# Админ-панель (упрощённая версия)
@app.route('/admin')
@login_required
def admin_dashboard():
    # Проверяем, является ли пользователь администратором
    if not current_user.is_admin:
        return redirect(url_for('index'))

    # Собираем статистику для админ-панели
    total_ideas = Idea.query.count()  # Общее количество идей
    total_users = User.query.count()  # Общее количество пользователей

    # Идеи по категориям для статистики
    categories = db.session.query(
        Idea.category,
        db.func.count(Idea.id)
    ).group_by(Idea.category).all()

    # Идеи по статусам для статистики
    statuses = db.session.query(
        Idea.status,
        db.func.count(Idea.id)
    ).group_by(Idea.status).all()

    # Отображаем админ-панель с собранной статистикой
    return render_template('admin/dashboard.html',
                           total_ideas=total_ideas,
                           total_users=total_users,
                           categories=categories,
                           statuses=statuses)


# API для голосования за идею (добавляем эту функцию)
@app.route('/api/ideas/<int:idea_id>/vote', methods=['POST'])
@login_required
def vote_idea(idea_id):
    try:
        data = request.json
        vote_type = data.get('vote_type')  # 'up' или 'down'

        # Проверяем, голосовал ли уже пользователь
        idea = Idea.query.get_or_404(idea_id)

        if vote_type == 'up':
            idea.votes_count += 1
        elif vote_type == 'down' and idea.votes_count > 0:
            idea.votes_count -= 1

        db.session.commit()

        return jsonify({'success': True, 'votes_count': idea.votes_count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


# Страница с информацией о городе
@app.route('/city')
def city_info():
    return render_template('city.html')


# API для получения статистики (для главной страницы)
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    total_ideas = Idea.query.count()
    total_users = User.query.count()

    return jsonify({
        'total_ideas': total_ideas,
        'total_users': total_users
    })


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@ecocity-rubtsovsk.ru',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print('Администратор создан: логин - admin, пароль - admin123')

    print(f"Сервер Эко-Город для Рубцовска запускается...")
    print(f"Координаты центра карты: {app.config['MAP_CENTER']}")
    print(f"Внутренний адрес: http://localhost:5000")
    print(f"Внешний адрес: http://[ваш IP адрес]:5000")
    print("Для доступа из интернета потребуется настройка проброса портов в роутере")

    # КЛЮЧЕВАЯ ИЗМЕНЕНИЯ:
    app.run(
        debug=True,
        port=5000,
        host='0.0.0.0'  # Разрешаем доступ со всех интерфейсов
    )