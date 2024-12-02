import paho.mqtt.client as mqtt
import sqlite3
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # для импорта config
from config import *
from database import get_moisture_settings

class MoistureController:
    def __init__(self):
        self.client = mqtt.Client("moisture_controller")
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        self.client.connect(MQTT_BROKER, MQTT_PORT)
        
        # Подписываемся на топик с данными датчика
        self.client.on_message = self.on_message
        self.client.subscribe(MQTT_TOPIC_SENSOR)
        
        self.current_moisture = None
        self.last_watering_time = 0
        self.is_watering = False
        self.client.loop_start()
    
    def on_message(self, client, userdata, msg):
        """Обработка входящих сообщений"""
        try:
            if msg.topic == MQTT_TOPIC_SENSOR:
                # Получили новые данные от датчика
                self.current_moisture = float(msg.payload.decode())
                self.check_and_control()
                
        except Exception as e:
            print(f"Ошибка обработки сообщения: {e}")
    
    def check_and_control(self):
        """Проверка условий и управление насосом"""
        if self.current_moisture  is None:
            return
            
        min_moisture, max_moisture = get_moisture_settings()
        current_time = time.time()
    
        # Логика полива с учетом дозированности
        if (self.current_moisture < min_moisture and 
            not self.is_watering and 
            current_time - self.last_watering_time > DRYING_PERIOD):
            
            # Включаем полив
            self.client.publish(MQTT_TOPIC_PUMP, "ON")
            self.is_watering = True
            self.last_watering_time = current_time
            print(f"Старт полива. Влажность: {self.current_moisture}%")
        
        # Контроль окончания полива
        if self.is_watering:
            if current_time - self.last_watering_time >= WATERING_DURATION:
                self.client.publish(MQTT_TOPIC_PUMP, "OFF")
                self.is_watering = False
                print(f"Полив остановлен. Влажность: {self.current_moisture}%")

        print(f"Текущая влажность: {self.current_moisture}%, " + 
              f"мин: {min_moisture}%, " + 
              f"макс: {max_moisture}%, " + 
              f"статус: {'Полив' if self.is_watering else 'Ожидание'}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()

if __name__ == "__main__":
    controller = MoistureController()
    try:
        print("Контроллер запущен")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nКонтроллер остановлен")
    finally:
        controller.stop()