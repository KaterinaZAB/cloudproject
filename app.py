from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching.backends import SimpleCache

from flask_caching import Cache  # Импортируем модуль для кэширования
import os

# инициализация Flask приложения
app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, Docker!'

# Конфигурация для подключения к базе данных PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Настройка кэша (Redis как backend для кэша)
app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = os.getenv('REDIS_HOST', 'localhost')
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_REDIS_DB'] = 0
app.config['CACHE_REDIS_URL'] = f"redis://{app.config['CACHE_REDIS_HOST']}:{app.config['CACHE_REDIS_PORT']}/0"

# Инициализация SQLAlchemy, Flask-Migrate и кэша
db = SQLAlchemy(app)
migrate = Migrate(app, db)
cache = Cache(config={'CACHE_TYPE': 'flask_caching.backends.SimpleCache'})
cache.init_app(app)

# Модель для таблицы "User"
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Создание нового пользователя
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()  # Получаем данные из запроса
    new_user = User(username=data['username'], email=data['email'])  # Создаем нового пользователя
    db.session.add(new_user)  # Добавляем пользователя в сессию
    db.session.commit()  # Сохраняем изменения в базе данных
    return jsonify({'message': 'User created successfully'}), 201  # Возвращаем сообщение об успехе

# Получение всех пользователей с кэшированием
@app.route('/users', methods=['GET'])
@cache.cached(timeout=60)  # Данные будут кэшироваться на 60 секунд
def get_users():
    users = User.query.all()  # Получаем всех пользователей из базы данных
    users_list = [{'id': user.id, 'username': user.username, 'email': user.email} for user in users]  # Формируем список пользователей
    return jsonify(users_list)  # Возвращаем список пользователей в формате JSON

# Получение пользователя по ID
@app.route('/users/<int:id>', methods=['GET'])
@cache.cached(timeout=120, key_prefix='user_data')  # Используем key_prefix
def get_user(id):
    user = User.query.get(id)  # Находим пользователя по ID
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify({'id': id, 'username': id, 'email': id})

# Обновление пользователя
@app.route('/users/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get(id)  # Находим пользователя по ID
    data = request.get_json()  # Получаем данные из запроса
    if not user:  # Проверяем, найден ли пользователь
        return jsonify({'message': 'User not found'}), 404  # Возвращаем сообщение об ошибке, если пользователь не найден
    user.username = data.get('username', user.username)  # Обновляем имя пользователя, если передано новое значение
    user.email = data.get('email', user.email)  # Обновляем email, если передано новое значение
    db.session.commit()  # Сохраняем изменения в базе данных
    cache.clear()  # Очищаем кэш при изменении данных
    return jsonify({'message': 'User updated successfully'})  # Возвращаем сообщение об успехе

# Удаление пользователя
@app.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get(id)  # Находим пользователя по ID
    if not user:  # Проверяем, найден ли пользователь
        return jsonify({'message': 'User not found'}), 404  # Возвращаем сообщение об ошибке, если пользователь не найден
    db.session.delete(user)  # Удаляем пользователя из сессии
    db.session.commit()  # Сохраняем изменения в базе данных
    cache.clear()  # Очищаем кэш при удалении данных
    return jsonify({'message': 'User deleted successfully'})  # Возвращаем сообщение об успехе

# Пример маршрута с кэшированием данных
@app.route('/data')
@cache.cached(timeout=60)  # Данные будут кэшироваться на 60 секунд
def get_data():
    # Эмуляция долгого запроса (например, к базе данных)
    return jsonify({'data': 'This is some data!'})

# Очистка кэша для определенного пользователя
@app.route('/clear_cache/<int:id>')
def clear_user_cache(id):
    cache.delete(f'user_data::{id}')
    return jsonify({'message': f'Cache for user {id} cleared'})

# Запуск приложения
if __name__ == '__main__':
    app.run(host='0.0.0.0')  # Запускаем сервер на всех интерфейсах
