import time
import random
import paho.mqtt.client as mqtt
import threading
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # для импорта config
from config import *

class MoistureSensor:
    """Симулятор датчика влажности"""
    def __init__(self):
        self.client = mqtt.Client("moisture_sensor")
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)

        self.current_moisture = 50.0
        self.pump_is_active = False
        
        # Подписываемся на состояние насоса
        self.client.on_message = self.on_message
        self.client.subscribe(MQTT_TOPIC_PUMP)
        self.client.loop_start()

    def on_message(self, client, userdata, msg):
        """Отслеживаем состояние насоса"""
        if msg.topic == MQTT_TOPIC_PUMP:
            command = msg.payload.decode()
            self.pump_is_active = (command == "ON")
            print(f"Статус насоса: {command}")

    def simulate(self):
        """Одно измерение освещенности"""
        # Симуляция изменения влажности
        if self.pump_is_active:
            # Быстрое повышение влажности при поливе
            self.current_moisture += random.uniform(5, 15)
        else:
            # Естественное снижение влажности
            self.current_moisture -= random.uniform(2, 5)

        self.current_moisture = max(0, min(100, self.current_moisture))

        # Публикация значения влажности
        self.client.publish(MQTT_TOPIC_SENSOR, f"{self.current_moisture:.1f}")
        print(f"Текущая влажность: {self.current_moisture:.1f}% " + 
                f"(Насос: {'Вкл' if self.pump_is_active else 'Выкл'})")
        # time.sleep(2)

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

class PumpControl:
    """Симулятор насоса"""
    def __init__(self):
        self.client = mqtt.Client("pump_control")
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.connect(MQTT_BROKER, MQTT_PORT, 60)
        self.is_active = False
        # Подписка на команды управления 
        self.client.on_message = self.on_message
        self.client.subscribe(MQTT_TOPIC_PUMP)
        self.client.loop_start()  
    
    def on_message(self, client, userdata, msg):
        """Обработка команд включения/выключения"""
        command = msg.payload.decode()
        self.is_active = (command == "ON")
        print(f"Состояние насоса изменено на: {'ON' if self.is_active else 'OFF'}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

def run_sensor(sensor):
    try:
        print("Запуск симуляции датчика влажности")
        while True:
            sensor.simulate()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка симуляции датчика влажности")
        sensor.stop()

def run_control(control):
    try:
        print("Запуск симулятора насоса")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка симулятора насоса")
        control.stop()

if __name__ == "__main__":
    sensor = MoistureSensor()
    pump = PumpControl()
    
    # Запуск в отдельных потоках
    sensor_thread = threading.Thread(target=run_sensor, args=(sensor,))
    pump_thread = threading.Thread(target=run_control, args=(pump,))
    
    sensor_thread.start()
    pump_thread.start()

    try:
        sensor_thread.join()
        pump_thread.join()
    except KeyboardInterrupt:
        print("\nОстановка симуляции")