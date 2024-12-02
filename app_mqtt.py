from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
import sqlite3
import paho.mqtt.client as mqtt
from config import *
from database import init_db, save_moisture_data, get_moisture_history
from utils import verify_password
from datetime import datetime

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Глобальные переменные для хранения текущих данных
current_data = {
    'timestamp': None,
    'moisture_level': None,
    'pump_status': 'OFF'
}

# Настройка MQTT клиента
mqtt_client = mqtt.Client("web_client")


def on_mqtt_message(client, userdata, msg):
    """Обработка входящих MQTT сообщений"""
    try:
        if msg.topic == MQTT_TOPIC_SENSOR:
            moisture_level = float(msg.payload.decode())
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            current_data['moisture_level'] = moisture_level
            current_data['timestamp'] = timestamp
             # Сохраняем данные в базу при каждом новом измерении
            save_moisture_data(timestamp, moisture_level)
        elif msg.topic == MQTT_TOPIC_PUMP:
            current_data['pump_status'] = msg.payload.decode()
    except Exception as e:
        print(f"Ошибка обработки MQTT сообщения: {e}")

# Настройка MQTT подключения
def setup_mqtt():
    mqtt_client.on_message = on_mqtt_message
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.subscribe([(MQTT_TOPIC_SENSOR, 0), (MQTT_TOPIC_PUMP, 0)])
    mqtt_client.loop_start()

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
        max_moisture = float(request.form['max_moisture'])
        
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

@app.route('/api/current_moisture')
@login_required
def current_moisture():
    """Получение текущих данных о влажности почты"""
    return jsonify({
        'timestamp': current_data['timestamp'],
        'moisture_level': current_data['moisture_level'],
        'pump_status': current_data['pump_status']
    })

@app.route('/api/moisture_history')
@login_required
def moisture_history():
    """Получение истории измерений показаний"""
    history = get_moisture_history()
    return jsonify(history)

if __name__ == '__main__':
    init_db()
    setup_mqtt()
    app.run(debug=True, use_reloader=False)  # use_reloader=False важно при использовании MQTT