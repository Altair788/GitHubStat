import json
import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import psycopg2
from psycopg2 import OperationalError, InterfaceError


class AbstractDBManager(ABC):
    """
    Представляет абстрактный класс AbstractDBManager.
    """

    @abstractmethod
    def drop_db(self, dbname: str) -> None:
        """
        Удаляет БД
        Args:
             dbname(str): наименование БД
        """
        pass

    @abstractmethod
    def insert_data_to_table(self, data: list[dict[str, Any]], table: str) -> None:
        """
        Заполняет таблицу данными

        Args:
            data(list(dict(str, Any))): список словарей
            table(str): наименование таблицы
        """
        pass

    @abstractmethod
    def get_data_from_table(self, table: str, count: int) -> list[dict[str, Any]]:
        """
        Получает данные из таблицы

        Args:
            table(str): название таблицы
            count(int): лимит вывода
        Returns:
            list[dict[str, Any]]: список словарей
        """
        pass

    @abstractmethod
    def export_data_to_JSON(self, table: str) -> None:
        """
        Экспортирует файлы из списка словарей, полученного из таблицы, в файл (по ссылке)
        в формате JSON

        Args:
             table(str): название таблицы
        """
        pass

    @abstractmethod
    def drop_table(self, table: str) -> None:
        """
        Абстрактный метод для удаления таблицы.

        Args:
             table(str): наименование таблицы.

        """
        pass


class PostgresDB(AbstractDBManager):
    """
    Представляет класс PostgresDB, который обеспечивает взаимодействие с БД.
    Реализует методы, чтобы создать таблицу, добавить данные в таблицу,
    экспортировать данные в формат JSON и получить данные из таблицы.
    Наследует функциональность от абстрактного класса AbstractDBManager.
    """

    def __init__(self, params):
        self.dbname: str = params["dbname"]
        self.user: str = params["user"]
        self.password: str = params["password"]
        self.host: str = params["host"]
        self.port: int = params["port"]
        self.conn = psycopg2.connect(dbname="postgres", user=self.user, password=self.password,
                                     host=self.host, port=self.port)
        self.conn.autocommit = True

        cur = self.conn.cursor()

        cur.execute(f'DROP DATABASE if exists {self.dbname};')
        cur.execute(f'CREATE DATABASE {self.dbname};')

        cur.close()
        print(f"База данных '{self.dbname}' успешно создана.")
        self.conn.close()
        self.conn = psycopg2.connect(dbname=self.dbname, user=self.user, password=self.password,
                                     host=self.host, port=self.port)
        self.conn.autocommit = True
        print(f"Соединение БД '{self.dbname}' успешно установлено.")

    def create_table(self, table_name: str) -> None:
        """
        Создание таблиц для сохранения данных
        """
        if table_name == "repos":
            with self.conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS repos (
                    id SERIAL PRIMARY KEY,
                    repo_name VARCHAR(225) NOT NULL,
                    repo_url TEXT NOT NULL
                );
                """)

        elif table_name == "contributors":
            with self.conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS contributors(
                    id SERIAL PRIMARY KEY,
                    contributor_name VARCHAR(100) NOT NULL,
                    total_commits INTEGER NOT NULL,
                    weekly_timestamp INTEGER NOT NULL,
                    weekly_lines_added INTEGER NOT NULL,
                    weekly_lines_deleted INTEGER NOT NULL,
                    weekly_commit_count INTEGER NOT NULL,
                    repo_id INTEGER NOT NULL,
                    FOREIGN KEY (repo_id) REFERENCES repos(id)
                );
                """)
        else:
            print("Таблицу с таким именем создать нельзя: используйте для создания имена 'repos', 'contributors'")
        self.conn.commit()

    def insert_data_to_table(self, data: list[dict[str, Any]], table: str) -> None:
        """
        Заполняет таблицу данными.

        Args:
             data: list[dict[str, Any]]: список словарей с данными из GitHub
             table(str): наименование таблицы
        """

        if table == "repos":
            with self.conn.cursor() as cur:
                sql = """
                INSERT INTO repos (repo_name, repo_url) VALUES (%s, %s);
            """
                for item in data:
                    cur.execute(sql, (item["repo_name"], item["repo_url"]))

            self.conn.commit()

        elif table == "contributors":
            with self.conn.cursor() as cur:
                sql = f"""
                INSERT INTO contributors (contributor_name, total_commits, weekly_timestamp, weekly_lines_added,
                 weekly_lines_deleted, weekly_commit_count, repo_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
                for item in data:
                    repo_id = self.get_repo_id(item["repo_name"])
                    cur.execute(sql, (item["contributor_name"], item["total_commits"], item["weekly_timestamp"],
                                      item["weekly_lines_added"], item["weekly_lines_deleted"],
                                      item["weekly_commit_count"], repo_id))

            self.conn.commit()

        else:
            raise ValueError(f"Таблица '{table}' не найдена.")

    def get_repo_id(self, repo_name: str) -> int:
        """
        Получает идентификатор репозитория по его имени.

        Args:
            repo_name (str): имя репозитория

        Returns:
            int: идентификатор репозитория
        """
        with self.conn.cursor() as cur:
            sql = "SELECT id FROM repos WHERE repo_name = %s;"
            cur.execute(sql, (repo_name,))
            result = cur.fetchone()
            if result:
                return result[0]  # Возвращаем id репозитория
            else:
                raise ValueError(f"Репозиторий '{repo_name}' не найден.")

    def drop_table(self, table: str) -> None:
        """
        Удаляет таблицу, если она существует.

        Args:
             table(str): наименование таблицы.
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                   DROP TABLE IF EXISTS {table};
               """)
        self.conn.commit()

    def drop_db(self, dbname: str) -> None:
        """
        Удаляет БД, если она существует.

        Args:
             dbname(str): наименование БД.
        """
        # Закрываем текущее соединение, если оно есть
        if self.conn:
            self.close()

        self.conn = psycopg2.connect(dbname="postgres", user=self.user, password=self.password,
                                     host=self.host, port=self.port)
        self.conn.autocommit = True  # Включаем автокоммит
        with self.conn.cursor() as cur:
            # Удаляем базу данных
            cur.execute(f"DROP DATABASE IF EXISTS {dbname};")
        self.conn.commit()  # Фиксируем изменения
        print(f"База данных '{dbname}' успешно удалена, если она существовала.")

    def get_data_from_table(self, table: str, count: int) -> list[dict[str, Any]]:
        """
        Получает данные из таблицы.

        Args:
            table (str): название таблицы.
            count (int): количество записей для получения.

        Returns:
            list[dict[str, Any]]: список словарей с данными.
        """
        # Проверка на допустимые имена таблиц
        valid_tables = ["repos", "contributors"]
        if table not in valid_tables:
            raise ValueError(f"Недопустимое имя таблицы: {table}. Допустимые таблицы: {', '.join(valid_tables)}.")

        try:
            if table == "repos":
                with self.conn.cursor() as cur:
                    # Формируем SQL-запрос с использованием f-строки для имени таблицы
                    query = f"""
                        SELECT * FROM {table}
                        ORDER BY repo_name
                        LIMIT %s
                    """
                    cur.execute(query, (count,))
                    data = cur.fetchall()
                    data_dict = [
                        {
                            "repo_name": d[1],
                            "repo_url": d[2]
                        } for d in data
                    ]
                    return data_dict
            elif table == "contributors":
                with self.conn.cursor() as cur:
                    # Формируем SQL-запрос с использованием f-строки для имени таблицы
                    query = f"""
                        SELECT * FROM {table}
                        ORDER BY weekly_lines_added
                        LIMIT %s
                    """
                    cur.execute(query, (count,))
                    data = cur.fetchall()
                    data_dict = [
                        {
                            "contributor_name": d[1],
                            "total_commits": d[2],
                            "weekly_timestamp": d[3],
                            "weekly_lines_added": d[4],
                            "weekly_lines_deleted": d[5],
                            "weekly_commit_count": d[6],
                            "repo_id": d[7]
                        } for d in data
                    ]
                    return data_dict
        except psycopg2.DatabaseError as db_error:
            logging.error(f"Ошибка базы данных при получении данных из таблицы '{table}': {db_error}")
            return []  # Возвращаем пустой список в случае ошибки
        except Exception as e:
            logging.error(f"Неизвестная ошибка при получении данных из таблицы '{table}': {e}")
            return []  # Возвращаем пустой список в случае ошибки

    def export_data_to_JSON(self, table: str) -> None:
        """
        Экспортирует файлы из списка словарей, полученного из таблицы, в файл (по ссылке)
        в формате JSON

        Args:
             table(str): название таблицы
        """
        valid_tables = ["repos", "contributors"]
        if table not in valid_tables:
            raise ValueError(f"Недопустимое имя таблицы: {table}. Допустимые таблицы: {', '.join(valid_tables)}.")

        try:
            if table == "repos":
                with self.conn.cursor() as cur:
                    # Формируем SQL-запрос с использованием f-строки для имени таблицы
                    query = f"""
                        SELECT * FROM {table};
                    """
                    cur.execute(query, )
                    data = cur.fetchall()
                    data_dict = [
                        {
                            "repo_name": d[1],
                            "repo_url": d[2]
                        } for d in data
                    ]

            elif table == "contributors":
                with self.conn.cursor() as cur:
                    # Формируем SQL-запрос с использованием f-строки для имени таблицы
                    query = f"""
                        SELECT * FROM {table};
                    """
                    cur.execute(query, )
                    data = cur.fetchall()
                    data_dict = [
                        {
                            "contributor_name": d[1],
                            "total_commits": d[2],
                            "weekly_timestamp": d[3],
                            "weekly_lines_added": d[4],
                            "weekly_lines_deleted": d[5],
                            "weekly_commit_count": d[6],
                            "repo_id": d[7]
                        } for d in data
                    ]

        except psycopg2.DatabaseError as db_error:
            logging.error(f"Ошибка базы данных при получении данных из таблицы '{table}': {db_error}")
            return []  # Возвращаем пустой список в случае ошибки
        except Exception as e:
            logging.error(f"Неизвестная ошибка при получении данных из таблицы '{table}': {e}")
            return []  # Возвращаем пустой список в случае ошибки

        # Создаем путь к файлу
        file_path = os.path.join("src", "data", f"{table}.json")

        # Открываем файл для записи
        with open(file_path, "w") as f:
            json.dump(data_dict, f, indent=4)

        print(f"Данные успешно сохранены в {file_path}")

    def close(self):
        """Закрывает текущее соединение с базой данных."""
        if self.conn:
            try:
                self.conn.close()
                print("Соединение с базой данных закрыто.")
            except (OperationalError, InterfaceError) as e:
                print(f"Ошибка при закрытии соединения: {e}")
            except Exception as e:
                print(f"Неизвестная ошибка при закрытии соединения: {e}")
