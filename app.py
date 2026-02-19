import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config

app = Flask(__name__, static_folder='staticCSS')
app.config.from_object(Config)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
with app.app_context():
    db.create_all()
    print("Таблицы созданы (или уже существуют).")

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
                           map_zoom=app.config['MAP_ZOOM'])

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
        # Простейшая валидация
        if not data.get('title') or not data.get('description'):
            return jsonify({'success': False, 'error': 'Заполните все поля'}), 400

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
        # 👇 Логируем ошибку в консоль (будет видно в логах Render)
        print(f"❌ Ошибка при создании идеи: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        if not username or not email or not password:
            flash('Заполните все обязательные поля')
            return redirect(url_for('register'))
        if password != confirm_password:
            flash('Пароли не совпадают')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован')
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
    return render_template('auth/register.html')

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
            flash('Неверное имя пользователя или пароль')
    return render_template('auth/login.html')

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

if __name__ == '__main__':
    # Создаём папки (если их нет) – это можно оставить, т.к. выполняется только локально
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
        print(f"Создана папка instance: {instance_path}")

    uploads_path = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
    if not os.path.exists(uploads_path):
        os.makedirs(uploads_path)
        print(f"Создана папка uploads: {uploads_path}")

    # 👇 УБИРАЕМ db.create_all() отсюда – теперь оно выполняется выше
    # with app.app_context():
    #     db.create_all()   # <-- больше не нужно здесь

    print(f"Сервер Эко-Город для Рубцовска запускается...")
    print(f"Координаты центра карты: {app.config['MAP_CENTER']}")
    print(f"База данных: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Откройте в браузере: http://localhost:5000")
    app.run(debug=True, port=5000)