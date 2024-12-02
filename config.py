DB_NAME = "moisture_control.db"
SECRET_KEY = "secret-key"
# Настройки для MQTT
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
MQTT_USERNAME = "test_username"
MQTT_PASSWORD = "test_password"
MQTT_TOPIC_SENSOR = "garden/moisture"
MQTT_TOPIC_PUMP = "garden/pump"
# Настройки для HTTP
SENSOR_URL = "http://127.0.0.1:5001"  # URL симулятора датчика света
PUMP_URL = "http://127.0.0.1:5002"   # URL симулятора светильника

# Параметры полива
MIN_MOISTURE = 30  # Нижний порог влажности для запуска полива 
MAX_MOISTURE = 70  # Верхний порог влажности
WATERING_DURATION = 3  # Длительность полива в секундах
DRYING_PERIOD = 5  # Период высыхания почвы