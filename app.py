import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import func
from config import Config

app = Flask(__name__, static_folder='staticCSS')
app.config.from_object(Config)

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'


# =========================
# МОДЕЛИ
# =========================

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
    views_count = db.Column(db.Integer, default=0)
    author = db.relationship('User', backref='ideas', lazy=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =========================
# INIT DATABASE
# =========================

_db_initialized = False


@app.before_request
def initialize_database():
    global _db_initialized
    if not _db_initialized:
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@eco-city.ru',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()

            test = Idea(
                title='Тестовая идея',
                description='Проверка системы',
                category='озеленение',
                latitude=51.527623,
                longitude=81.217673,
                user_id=admin.id,
                votes_count=5,
                status='approved'
            )
            db.session.add(test)
            db.session.commit()
        _db_initialized = True


# =========================
# ПУБЛИЧНЫЕ СТРАНИЦЫ
# =========================

@app.route('/')
def index():
    recent_ideas = Idea.query.order_by(Idea.created_at.desc()).limit(3).all()
    total_ideas = Idea.query.count()
    total_users = User.query.count()
    return render_template(
        'index.html',
        recent_ideas=recent_ideas,
        total_ideas=total_ideas,
        total_users=total_users
    )


@app.route('/map')
def map_view():
    categories = db.session.query(Idea.category).distinct().all()
    categories = [c[0] for c in categories]
    return render_template(
        'map.html',
        map_center=app.config['MAP_CENTER'],
        map_zoom=app.config['MAP_ZOOM'],
        categories=categories
    )


@app.route('/city')
def city_info():
    return render_template('city.html')


# =========================
# АУТЕНТИФИКАЦИЯ
# =========================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if password != confirm:
            flash('Пароли не совпадают')
            return redirect(url_for('register'))

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Неверный логин или пароль')
    return render_template('auth/login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# =========================
# ПУБЛИЧНОЕ API (ИДЕИ)
# =========================

@app.route('/api/ideas')
def get_ideas():
    ideas = Idea.query.all()
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
            'views_count': idea.views_count,
            'author': idea.author.username,
            'created_at': idea.created_at.isoformat()
        })
    return jsonify(result)


@app.route('/api/ideas', methods=['POST'])
@login_required
def create_idea():
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
    return jsonify({'success': True})


@app.route('/api/ideas/<int:idea_id>')
def get_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    # Увеличиваем счётчик просмотров
    idea.views_count += 1
    db.session.commit()
    return jsonify({
        'id': idea.id,
        'title': idea.title,
        'description': idea.description,
        'category': idea.category,
        'latitude': idea.latitude,
        'longitude': idea.longitude,
        'status': idea.status,
        'votes_count': idea.votes_count,
        'views_count': idea.views_count,
        'author': idea.author.username,
        'created_at': idea.created_at.isoformat()
    })


@app.route('/api/ideas/<int:idea_id>/vote', methods=['POST'])
@login_required
def vote(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    idea.votes_count += 1
    db.session.commit()
    return jsonify({'success': True})


# =========================
# АДМИНСКИЕ СТРАНИЦЫ (ТОЛЬКО ДЛЯ АДМИНОВ)
# =========================

@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))

    total_ideas = Idea.query.count()
    total_users = User.query.count()
    total_votes = db.session.query(func.sum(Idea.votes_count)).scalar() or 0

    categories = db.session.query(
        Idea.category,
        func.count(Idea.id)
    ).group_by(Idea.category).all()

    statuses = db.session.query(
        Idea.status,
        func.count(Idea.id)
    ).group_by(Idea.status).all()

    return render_template(
        'dashboard.html',  # файл лежит в корне templates
        total_ideas=total_ideas,
        total_users=total_users,
        total_votes=total_votes,
        categories=categories,
        statuses=statuses
    )


@app.route('/admin/ideas')
@login_required
def admin_ideas():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    return render_template('ideas.html')


@app.route('/admin/ideas/<int:idea_id>/edit')
@login_required
def admin_edit_idea(idea_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    idea = Idea.query.get_or_404(idea_id)
    return render_template('edit_idea.html', idea=idea)


@app.route('/admin/statistics')
@login_required
def admin_statistics():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    return render_template('statistics.html')


# =========================
# АДМИНСКОЕ API
# =========================

@app.route('/api/admin/all-ideas')
@login_required
def admin_all_ideas():
    if not current_user.is_admin:
        return jsonify({'error': 'access denied'}), 403

    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')

    query = Idea.query

    if search:
        query = query.filter(Idea.title.ilike(f'%{search}%'))
    if status:
        query = query.filter(Idea.status == status)
    if category:
        query = query.filter(Idea.category == category)

    if sort == 'newest':
        query = query.order_by(Idea.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Idea.created_at.asc())
    elif sort == 'votes':
        query = query.order_by(Idea.votes_count.desc())
    elif sort == 'title':
        query = query.order_by(Idea.title.asc())

    total = query.count()
    ideas = query.offset((page - 1) * limit).limit(limit).all()

    result = []
    for idea in ideas:
        result.append({
            'id': idea.id,
            'title': idea.title,
            'category': idea.category,
            'author': idea.author.username,
            'status': idea.status,
            'votes_count': idea.votes_count,
            'views_count': idea.views_count,
            'created_at': idea.created_at.isoformat()
        })

    return jsonify({
        'ideas': result,
        'total': total,
        'pages': (total + limit - 1) // limit
    })


@app.route('/api/admin/ideas/<int:idea_id>', methods=['PUT'])
@login_required
def admin_update_idea(idea_id):
    if not current_user.is_admin:
        return jsonify({'error': 'access denied'}), 403

    idea = Idea.query.get_or_404(idea_id)
    data = request.json

    idea.title = data.get('title', idea.title)
    idea.description = data.get('description', idea.description)
    idea.category = data.get('category', idea.category)
    idea.status = data.get('status', idea.status)
    idea.latitude = data.get('latitude', idea.latitude)
    idea.longitude = data.get('longitude', idea.longitude)
    idea.votes_count = data.get('votes_count', idea.votes_count)

    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/admin/ideas/<int:idea_id>', methods=['DELETE'])
@login_required
def admin_delete_idea(idea_id):
    if not current_user.is_admin:
        return jsonify({'error': 'access denied'}), 403

    idea = Idea.query.get_or_404(idea_id)
    db.session.delete(idea)
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/admin/ideas/<int:idea_id>/response', methods=['POST'])
@login_required
def admin_response(idea_id):
    if not current_user.is_admin:
        return jsonify({'error': 'access denied'}), 403

    idea = Idea.query.get_or_404(idea_id)
    data = request.json
    idea.status = data.get('status', idea.status)
    # Здесь можно сохранить комментарий администратора, если добавить поле в модель
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/admin/detailed-stats')
@login_required
def admin_stats():
    if not current_user.is_admin:
        return jsonify({'error': 'access denied'}), 403

    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    category = request.args.get('category', '')

    query = Idea.query

    if date_from:
        query = query.filter(Idea.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Idea.created_at <= datetime.fromisoformat(date_to))
    if category:
        query = query.filter(Idea.category == category)

    ideas = query.all()

    # Активность по дням
    daily = {}
    for idea in ideas:
        d = idea.created_at.strftime('%Y-%m-%d')
        daily[d] = daily.get(d, 0) + 1
    daily_activity = [{'date': k, 'count': v} for k, v in sorted(daily.items())]

    # Топ идей по голосам
    top_ideas = query.order_by(Idea.votes_count.desc()).limit(10).all()
    top_ideas_result = [{
        'id': idea.id,
        'title': idea.title,
        'author': idea.author.username,
        'votes_count': idea.votes_count,
        'category': idea.category
    } for idea in top_ideas]

    # Активные пользователи (упрощённо)
    users = User.query.all()
    top_users = []
    for user in users:
        top_users.append({
            'username': user.username,
            'ideas_count': len(user.ideas),
            'votes_given': 0,  # здесь можно добавить логику подсчёта голосов пользователя
            'comments_count': 0
        })

    return jsonify({
        'daily_activity': daily_activity,
        'top_ideas': top_ideas_result,
        'top_users': top_users
    })


# =========================
# ЗАПУСК
# =========================

if __name__ == '__main__':
    print("Eco City Server started")
    app.run(debug=True, port=5000)