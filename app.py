import os
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Модели
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(50), default='Рубцовск')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    votes_count = db.Column(db.Integer, default=0)
    author = db.relationship('User', backref='ideas', lazy=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Создание таблиц при первом запросе (если их нет)
@app.before_request
def create_tables():
    # Проверяем, созданы ли таблицы, по наличию таблицы 'user'
    if not hasattr(app, 'tables_created'):
        try:
            db.create_all()
            # Добавляем администратора по умолчанию, если его нет
            if not User.query.filter_by(username='admin').first():
                admin = User(
                    username='admin',
                    email='admin@ecocity-rubtsovsk.ru',
                    password_hash=generate_password_hash('admin123'),
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                logger.info("Администратор создан: admin / admin123")
            # Добавляем тестовые идеи, если таблица пуста
            if Idea.query.count() == 0:
                test_ideas = [
                    Idea(
                        title='Создание нового парка на Ленина',
                        description='Зелёная зона с детской площадкой и скамейками',
                        category='озеленение',
                        latitude=51.527623,
                        longitude=81.217673,
                        user_id=1,
                        votes_count=15,
                        status='approved'
                    ),
                    Idea(
                        title='Ремонт тротуара на Советской',
                        description='Тротуар требует срочного ремонта',
                        category='безопасность',
                        latitude=51.525000,
                        longitude=81.220000,
                        user_id=1,
                        votes_count=8,
                        status='pending'
                    ),
                    Idea(
                        title='Установка велопарковок в центре',
                        description='Парковки у магазинов и учреждений',
                        category='транспорт',
                        latitude=51.530000,
                        longitude=81.215000,
                        user_id=1,
                        votes_count=12,
                        status='approved'
                    )
                ]
                db.session.add_all(test_ideas)
                db.session.commit()
                logger.info("Тестовые идеи добавлены.")
            app.tables_created = True
        except Exception as e:
            logger.error(f"Ошибка при создании таблиц: {e}")

# Маршруты
@app.route('/')
def index():
    recent_ideas = Idea.query.order_by(Idea.created_at.desc()).limit(3).all()
    total_ideas = Idea.query.count()
    total_users = User.query.count()
    return render_template('index.html',
                           recent_ideas=recent_ideas,
                           total_ideas=total_ideas,
                           total_users=total_users)

@app.route('/map')
def map_view():
    categories = ['спорт', 'культура', 'экология', 'озеленение', 'безопасность', 'другое']
    return render_template('map.html',
                           categories=categories,
                           map_center=app.config['MAP_CENTER'],
                           map_zoom=app.config['MAP_ZOOM'],
                           map_tiles=app.config['MAP_TILES'])

@app.route('/api/ideas', methods=['GET'])
def get_ideas():
    category = request.args.get('category')
    status = request.args.get('status')
    query = Idea.query
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    ideas = query.all()
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
    return jsonify(result)

@app.route('/api/ideas', methods=['POST'])
@login_required
def create_idea():
    try:
        data = request.json
        idea = Idea(
            title=data['title'],
            description=data['description'],
            category=data['category'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            user_id=current_user.id
        )
        db.session.add(idea)
        db.session.commit()
        return jsonify({'success': True, 'id': idea.id})
    except Exception as e:
        logger.error(f"Ошибка создания идеи: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

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

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        city = request.form.get('city', 'Рубцовск')

        # Валидация
        if not username or not email or not password:
            flash('Заполните все обязательные поля', 'danger')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'danger')
            return redirect(url_for('register'))

        try:
            if User.query.filter_by(email=email).first():
                flash('Email уже зарегистрирован', 'danger')
                return redirect(url_for('register'))

            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                city=city
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash(f'Добро пожаловать, {username}!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя {username}: {e}")
            db.session.rollback()
            flash('Произошла ошибка при регистрации. Пожалуйста, попробуйте позже.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')  # путь без 'auth/'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    return render_template('login.html')  # путь без 'auth/'

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    total_ideas = Idea.query.count()
    total_users = User.query.count()
    total_votes = db.session.query(db.func.sum(Idea.votes_count)).scalar() or 0
    categories = db.session.query(
        Idea.category,
        db.func.count(Idea.id)
    ).group_by(Idea.category).all()
    statuses = db.session.query(
        Idea.status,
        db.func.count(Idea.id)
    ).group_by(Idea.status).all()
    return render_template('admin/dashboard.html',
                           total_ideas=total_ideas,
                           total_users=total_users,
                           total_votes=total_votes,
                           categories=categories,
                           statuses=statuses)

@app.route('/api/ideas/<int:idea_id>/vote', methods=['POST'])
@login_required
def vote_idea(idea_id):
    try:
        data = request.json
        vote_type = data.get('vote_type')
        idea = Idea.query.get_or_404(idea_id)
        if vote_type == 'up':
            idea.votes_count += 1
        elif vote_type == 'down' and idea.votes_count > 0:
            idea.votes_count -= 1
        db.session.commit()
        return jsonify({'success': True, 'votes_count': idea.votes_count})
    except Exception as e:
        logger.error(f"Ошибка голосования за идею {idea_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/city')
def city_info():
    return render_template('city.html')

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    total_ideas = Idea.query.count()
    total_users = User.query.count()
    return jsonify({
        'total_ideas': total_ideas,
        'total_users': total_users
    })

@app.route('/admin/ideas')
@login_required
def admin_ideas():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    return render_template('admin/ideas.html')

@app.route('/admin/statistics')
@login_required
def admin_statistics():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    return render_template('admin/statistics.html')

@app.route('/api/admin/all-ideas')
@login_required
def admin_all_ideas():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    ideas = Idea.query.all()
    return jsonify({
        'ideas': [{
            'id': i.id,
            'title': i.title,
            'category': i.category,
            'author': i.author.username,
            'status': i.status,
            'votes_count': i.votes_count,
            'views_count': 0,
            'created_at': i.created_at.isoformat()
        } for i in ideas],
        'total': len(ideas),
        'pages': 1
    })

if __name__ == '__main__':
    # Локальный запуск: создаём таблицы (если не созданы) и стартуем сервер
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)