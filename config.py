from pathlib import Path
from configparser import ConfigParser


def config(filename='database.ini', section='postgresql') -> dict[str, str]:
    """
    Конфигурируем БД из файла c конфигурационными установками.
    Args:
         filename: конфигурационные данные БД postgresql
         section(str): секция в конфигурационном файле
    Returns:
        db(dict): словарь с параметрами соединения, которые будут передаваться в DBManager() в дальнейшем.
    """
    # create a parser
    parser = ConfigParser()

    # read config file
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            if param[0] == "port":
                db[param[0]] = int(param[1])
            else:
                db[param[0]] = param[1]
    else:
        raise Exception(
            f"Section {section} is not found in the {filename}")
    return db
