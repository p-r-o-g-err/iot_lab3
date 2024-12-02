# Настройка окружения
1) python -m venv venv                  // создание виртуального окружения (при необходимости)
2) venv/scripts/activate.bat            // активация виртуального окружения
3) pip install -r requirements.txt      // установка зависимостей (при необходимости)

# Инструкция по запуску на протоколе mqtt
1) python mqtt/devices_simulator.py      // запуск эмуляторов актуатора и датчика
2) python mqtt/controller.py             // запуск контроллера
3) python app_mqtt.py                    // запуск основного flask приложения

# Инструкция по запуску на протоколе http
1) python http/devices_simulator.py      // запуск эмуляторов актуатора и датчика
2) python http/controller.py             // запуск контроллера
3) python app_http.py                    // запуск основного flask приложения
