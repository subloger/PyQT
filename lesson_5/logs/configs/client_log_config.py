""" Скрипт логирования клиентской части проекта """

import logging
import os
import sys

# регистратор событий
LOGGER = logging.getLogger("main.client")

# задание формата строки для записи в лог-файл
FORMAT = logging.Formatter("%(asctime)-25s"
                           " %(levelname)-10s "
                           "%(module)-20s"
                           " %(message)s")

# формирование пути
PATH = os.getcwd()
tail = os.path.split(PATH)[1]
if tail == "lesson_5":
    os.chdir("logs/log_files")
    PATH = os.getcwd() + "/client.log"
if tail == "configs":
    os.chdir(os.pardir)
    os.chdir("log_files")
    PATH = os.getcwd() + "/client.log"

# обработчик записи в файл
HANDLER = logging.FileHandler(PATH, "a", encoding="utf-8")

HANDLER.setFormatter(FORMAT)
LOGGER.addHandler(HANDLER)
LOGGER.setLevel(logging.DEBUG)

if __name__ == "__main__":
    TEST_LOGGER = logging.StreamHandler(sys.stderr)
    TEST_LOGGER.setFormatter(FORMAT)
    LOGGER.addHandler(TEST_LOGGER)
    LOGGER.debug('Отладочная информация')
    LOGGER.info('Информационное сообщение')
    LOGGER.warning('Внимание, предупреждение!')
    LOGGER.critical('Внимание, критическая ошибка!')
