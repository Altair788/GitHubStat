# Проект GitHubStat

## Описание
Проект GitHubStat позволяет собрать статистику по репозиториям заданного пользователя
на GitHub и сохранить ее в базу данных Postgres.


## Установка и запуск
1. Убедитесь, что у вас установлен Python версии 3.12.
2. Установите зависимости из файла `pyproject.toml`, используя Poetry:
    ```bash
    poetry install
    ```
3. Запустите приложение:
    ```bash
    python main.py
    ```

## Зависимости
Для работы проекта требуется установить зависимости, указанные в файле `pyproject.toml` и `poetry.lock`, включая:

- Python 3.12
- Библиотека pytest для тестирования (pytest 8.2.2).
- Библиотека pytest-cov для измерения покрытия кода тестами (pytest-cov 5.0.0).
- Библиотека requests для работы с HTTP запросами (requests 2.32.3).
- psycopg2 — это библиотека для работы с базами данных PostgreSQL в Python
- python-dotenv 1.0.1 — библиотека для загрузки переменных окружения из файла .env

## Структура проекта

- **main.py**: Главный файл проекта, ответственный за запуск.
- **config.py**: Содержит  функцию - конфигуратор БД - config.
- **database.ini**: Конфигурационный файл с данными для подключения к БД.
- **.env**: GITHUB_API_KEY

- **src/**: Директория с основными модулями:
    - **functions.py**: Модуль для работы с API, включает абстрактный класс API, класс Parser для парсинга 
    и обработки данных по вакансиям, родительский класс GitHubParser.
    - **postgres_db.py**: Модуль для работы с БД PostgreSQL. Включает абстрактный класс AbstractDBManager, 
    класс PostgresDB для манипуляций с данными и таблицами в БД.


- **tests/**: Директория для модульных тестов.

- **pyproject.toml**, **poetry.lock**: Файлы с зависимостями и конфигурацией Poetry.



## Автор
Eduard Slobodyanik <slobodyanik.ed@gmail.com>
