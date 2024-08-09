import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


class API(ABC):
    """
    Представляет абстрактный класс API для взаимодействия с различными сервисами.
    """

    @abstractmethod
    def get_repos_stats(self, username: str) -> list[dict[str, Any]]:
        """
        Собирает статистику по репозиториям заданного пользователя на GitHub
        Args:
            username(str): данные по пользователю,
            статистику по репозиториям которого будем получать
        Returns:
            list[dict[str, Any]]: список словарей, содержащих статистику по каждому репозиторию.
        """
        pass


class Parser(API):
    """
    Представляет родительский класс для парсинга и обработки данных.

    Наследует функциональность от абстрактного класса API.
    """
    __slots__ = ["__url", "__headers", "__api_key"]

    def __init__(self, url: str, headers: dict[str, Any]) -> None:
        """
        Конструктор класса Парсер.

        Args:
            url(str): url
            headers(dict[str, Any]): headers
        """
        self.__url = url
        self.__headers = headers

    @property
    def url(self):
        return self.__url

    @property
    def headers(self):
        return self.__headers


class GitHubParser(Parser):
    """
    Представляет класс для парсинга и обработки данных из GitHub.

    Наследует функциональность от абстрактного класса API.
    """

    def __init__(self, api_key: str | Path, url=None, headers=None) -> None:
        """
        Конструктор класса GitHubParser, который наследует функциональность от
        родительского класса Parser.
        Args:
            api_key(str | Path): API_KEY
        """
        super().__init__(url, headers)

        if url is None:
            self.__url = "https://api.github.com"
        self.__api_key = api_key
        if headers is None:
            self.__headers = {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {api_key}"
            }

    @property
    def api_key(self):
        return self.__api_key

    def get_repos_stats(self, username: str) -> list[dict[str, Any]]:
        """
        Собирает статистику по репозиториям заданного пользователя на GitHub
        Args:
            username(str): данные по пользователю,
            статистику по репозиториям которого будем получать
        Returns:
            list[dict[str, Any]]: список словарей, содержащих статистику по каждому репозиторию.
        """
        repos_stats = []

        #  Получаем список репозиториев пользователя
        url = f"{self.__url}/users/{username}/repos"

        try:

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            repos = response.json()

            for repo in repos:

                repo_name = repo['name']
                repo_url = f"https://api.github.com/repos/{username}/{repo_name}/stats/contributors"
                repo_response = requests.get(repo_url, headers=self.headers)

                try:
                    repo_response.raise_for_status()
                    if repo_response.text:

                        contributors = repo_response.json()

                        for contributor in contributors:
                            if isinstance(contributor, dict) and "author" in contributor:
                                contributor_name = contributor.get("author", {}).get("login", "Unknown contributor")
                                total_commits = contributor.get("total", 0)
                                if contributor["weeks"]:
                                    weekly_timestamp = contributor["weeks"][0].get("w")
                                    weekly_lines_added = contributor["weeks"][0].get("a")
                                    weekly_lines_deleted = contributor["weeks"][0].get("d")
                                    weekly_commit_count = contributor["weeks"][0].get("c")

                                    repo_stats = {
                                        "repo_name": repo_name,
                                        "repo_url": repo_url,
                                        "contributor_name": contributor_name,
                                        "total_commits": total_commits,
                                        "weekly_timestamp": weekly_timestamp,
                                        "weekly_lines_added": weekly_lines_added,
                                        "weekly_lines_deleted": weekly_lines_deleted,
                                        "weekly_commit_count": weekly_commit_count
                                    }
                                    repos_stats.append(repo_stats)
                                else:
                                    print(f"No weekly data for contributor {contributor_name}")
                    else:
                        print(f"Получен пустой ответ для репозитория {repo_name}")
                except requests.HTTPError as e:
                    if repo_response.status_code == 403 and "rate limit exceeded" in str(e):
                        print("Достигнут лимит запросов. Ожидание 60 секунд...")
                        time.sleep(60)  # Ждем 60 секунд перед повторной попыткой
                    else:
                        print(f"Ошибка при получении статистических данных {repo_name}: {e}")

        except requests.HTTPError as e:
            print(f"Ошибка при обращении к репозиториям пользователя {username}: {e}")

        return repos_stats


if __name__ == '__main__':
    load_dotenv()
    api_key = os.getenv("GITHUB_API_KEY")
    gh = GitHubParser(api_key)
    res = gh.get_repos_stats("Altair788")
    print(res)
