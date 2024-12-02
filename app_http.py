from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
from config import *
from database import init_db, get_moisture_history
from utils import verify_password
import requests

app = Flask(__name__)
app.secret_key = SECRET_KEY

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    if user:
        return User(user[0], user[1])
    return None

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Проверяем наличие специального флага формы
        if request.form.get('login_attempt') == 'true':
            username = request.form['username']
            password = request.form['password']
            
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT id, username, password FROM users WHERE username = ?",
                    (username,))
            user = c.fetchone()
            conn.close()
            
            if user and verify_password(user[2], password):
                login_user(User(user[0], user[1]))
                return redirect(url_for('index'))
            flash('Неверный логин или пароль')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def settings():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    if request.method == 'POST':
        min_moisture = float(request.form['min_moisture'])
        max_moisture= float(request.form['max_moisture'])
        
        # Проверка корректности введенных значений
        if min_moisture >= max_moisture:
            flash('Минимальный уровень влажности должен быть меньше максимального')
            return redirect(url_for('index'))
        
        # max_moisture = 100
        c.execute("""
            UPDATE moisture_settings 
            SET min_moisture = ?, max_moisture = ? 
            WHERE id = 1
        """, (min_moisture, max_moisture))
        conn.commit()
    
    c.execute("SELECT min_moisture, max_moisture FROM moisture_settings WHERE id = 1")
    settings = c.fetchone()
    conn.close()
    
    if request.method == 'POST':
        return redirect(url_for('index'))
    
    return jsonify({
        'min_moisture': settings[0], 
        'max_moisture': settings[1]
    })

is_watering = False
last_watering_time = 0

@app.route('/api/current_moisture')
@login_required
def current_moisture():
    """Получение текущих данных о влажности почты"""
    try:
        # Получаем последнюю запись из истории освещенности
        history = get_moisture_history()
        # Возвращаем последнюю запись (если есть)
        if history:
            last_record = history[-1]
            # Запрос для получения статуса насоса (чтобы не хранить актуальное значение в БД)
            response = requests.get(f'{SENSOR_URL}/pump_status')
            if response.status_code == 200:
                pump_status = response.json().get('status', 'OFF')
            else:
                pump_status = 'OFF'

            return jsonify({
                'timestamp': last_record['timestamp'],
                'moisture_level': last_record['moisture_level'],
                'pump_status': pump_status
            })
        else:
            return jsonify({'moisture_level': None, 'pump_status': 'OFF'}), 404
         
    except Exception as e:
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/moisture_history')
@login_required
def moisture_history():
    """Получение истории измерений показаний"""
    history = get_moisture_history()
    return jsonify(history)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, use_reloader=False)  # use_reloader=False важно при использовании MQTT