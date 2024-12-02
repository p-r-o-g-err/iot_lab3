from flask import Flask, request, jsonify
import random
import time
import threading

app_sensor = Flask(__name__)
app_pump = Flask(__name__)

class MoistureSensor:
    def __init__(self):
        self.current_moisture = 50.0
        self.pump_is_active = False

    def simulate(self):
        # Симуляция изменения влажности
        if self.pump_is_active:
            # Быстрое повышение влажности при поливе
            self.current_moisture += random.uniform(5, 15)
        else:
            # Естественное снижение влажности
            self.current_moisture -= random.uniform(2, 5)
        
        self.current_moisture = max(0, min(100, self.current_moisture))
        return round(self.current_moisture, 1)

@app_sensor.route('/moisture', methods=['GET'])
def get_moisture():
    global sensor
    return jsonify({
        'moisture_level': sensor.simulate(),
        'pump_status': 'ON' if sensor.pump_is_active else 'OFF'
    })

@app_sensor.route('/pump_status', methods=['GET', 'POST'])
def pump_status():
    global sensor
    if request.method == 'POST':
        sensor.pump_is_active = request.json.get('status', False)
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'ON' if sensor.pump_is_active else 'OFF'})

@app_pump.route('/control', methods=['POST'])
def control_pump():
    global sensor
    status = request.json.get('status', 'OFF')
    sensor.pump_is_active = (status == 'ON')
    return jsonify({'status': status})

def run_sensor_app():
    app_sensor.run(port=5001)

def run_pump_app():
    app_pump.run(port=5002)

if __name__ == "__main__":
    sensor = MoistureSensor()
    
    # Запуск серверов в отдельных потоках
    sensor_thread = threading.Thread(target=run_sensor_app)
    pump_thread = threading.Thread(target=run_pump_app)
    sensor_thread.start()
    pump_thread.start()

    sensor_thread.join()
    pump_thread.join()

    print("Запущены симуляторы устройств")