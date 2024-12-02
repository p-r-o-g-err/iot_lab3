import requests
import time
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # для импорта config
from config import *
from database import save_moisture_data, get_moisture_settings
from datetime import datetime

class MoistureController:
    def __init__(self):
        self.current_moisture = None
        self.last_watering_time = 0
        self.is_watering = False
        
    def check_and_control(self):
        """Проверка условий и управление насосом"""
        try:
            # Получаем данные о влажности
            response = requests.get(f"{SENSOR_URL}/moisture")
            sensor_data = response.json()
            self.current_moisture = sensor_data['moisture_level']
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Сохраняем данные в БД
            save_moisture_data(timestamp, self.current_moisture)

            min_moisture, max_moisture = get_moisture_settings()
            current_time = time.time()

            # Логика полива с учетом дозированности
            if (self.current_moisture < min_moisture and 
                not self.is_watering and 
                current_time - self.last_watering_time > DRYING_PERIOD):
                
                # Включаем полив
                requests.post(f"{PUMP_URL}/control", json={'status': 'ON'})
                self.is_watering = True
                self.last_watering_time = current_time
                print(f"Старт полива. Влажность: {self.current_moisture}%")
            
            # Контроль окончания полива
            if self.is_watering:
                if current_time - self.last_watering_time >= WATERING_DURATION:
                    requests.post(f"{PUMP_URL}/control", json={'status': 'OFF'})
                    self.is_watering = False
                    print(f"Полив остановлен. Влажность: {self.current_moisture}%")

            print(f"Текущая влажность: {self.current_moisture}%, " + 
                  f"мин: {min_moisture}%, " + 
                  f"макс: {max_moisture}%, " + 
                  f"статус: {'Полив' if self.is_watering else 'Ожидание'}")

        except Exception as e:
            print(f"Ошибка в контроллере: {e}")


if __name__ == "__main__":
    controller = MoistureController()
    try:
        print("Контроллер запущен")
        while True:
            controller.check_and_control()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nКонтроллер остановлен")