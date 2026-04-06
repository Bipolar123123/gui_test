1 Test Runner GUI

Графическое приложение для запуска тестов pytest с визуальным интерфейсом на Tkinter.

2 Возможности

- Обнаружение всех тестов в папке `tests/`
- Выбор отдельных тестов для запуска (чекбоксы)
- Фильтрация тестов по маркерам (slow, fast, integration)
- Запуск выбранных тестов или одиночного теста по двойному клику
- Цветовое выделение результатов (PASSED / FAILED)
- Прогресс-бар во время выполнения
- Отображение времени выполнения каждого теста
- Сохранение лога в текстовый файл
- Сборка в один `.exe` файл (Windows)

3 Требования

- Python 3.7+
- Установленные зависимости (см. `requirements.txt`)

4 Установка и запуск из исходников

1. Клонируйте репозиторий:
   git clone https://github.com/Bipolar123123/gui_test.git
   cd gui_test
2. Создайте виртуальное окружение (рекомендуется):

python -m venv venv
venv\Scripts\activate 
3. Установите зависимости:

pip install -r requirements.txt
4. Запустите приложение:

python gui\test_runner.py
5.Сборка исполняемого файла (.exe)

python -m PyInstaller --onefile --windowed --name "TestRunner" --add-data "tests;tests" --add-data "my_project;my_project" gui\test_runner.py
