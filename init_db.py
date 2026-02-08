import os
from app import app, db
from app import User, Idea
from werkzeug.security import generate_password_hash

with app.app_context():
    # Удаляем все таблицы (очистка для разработки)
    # db.drop_all()

    # Создаем все таблицы
    db.create_all()

    # Создаем администратора если его нет
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@ecocity-rubtsovsk.ru',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)

        # Создаем тестовые идеи
        ideas = [
            Idea(
                title='Создание нового парка на Ленина',
                description='Предлагаю создать зелёную зону отдыха с детской площадкой и скамейками',
                category='озеленение',
                latitude=51.527623,
                longitude=81.217673,
                user_id=1,
                votes_count=15,
                status='approved'
            ),
            Idea(
                title='Ремонт тротуара на Советской',
                description='Тротуар требует срочного ремонта, многие плиты разрушены',
                category='безопасность',
                latitude=51.525000,
                longitude=81.220000,
                user_id=1,
                votes_count=8,
                status='pending'
            ),
            Idea(
                title='Установка велопарковок в центре',
                description='Для развития велодвижения нужны парковки у магазинов и учреждений',
                category='транспорт',
                latitude=51.530000,
                longitude=81.215000,
                user_id=1,
                votes_count=12,
                status='approved'
            )
        ]

        for idea in ideas:
            db.session.add(idea)

        db.session.commit()
        print('База данных инициализирована!')
        print('Создан администратор: login=admin, password=admin123')
        print('Создано 3 тестовые идеи')
    else:
        print('База данных уже инициализирована')