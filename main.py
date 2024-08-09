import os

from dotenv import load_dotenv

from config import config
from src.functions import GitHubParser
from src.postgres_db import PostgresDB


def main():
    # Подключаемся к БД
    params = config()
    print(type(params["port"]))
    db = PostgresDB(params)
    # db.drop_db("github")
    db.create_table("repos")
    db.create_table("contributors")
    #
    #  Подключаемся к API
    load_dotenv()
    api_key = os.getenv("GITHUB_API_KEY")
    git_hub_api = GitHubParser(api_key)
    data = git_hub_api.get_repos_stats("Altair788")

    #  Сохраняем данные в БД
    db.insert_data_to_table(data, "repos")
    db.insert_data_to_table(data, "contributors")
    print(db.get_data_from_table("contributors", 2))
    print(db.get_data_from_table("repos", 3))
    db.export_data_to_JSON("repos")
    db.export_data_to_JSON("contributors")


if __name__ == '__main__':
    main()
