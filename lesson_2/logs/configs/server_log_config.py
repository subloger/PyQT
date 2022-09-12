""" Скрипт логирования серверной части проекта """

# import logging
import logging.handlers
import os
import sys

# регистратор событий
LOGGER = logging.getLogger("main.server")

# задание формата строки для записи в лог-файл
FORMAT = logging.Formatter("%(asctime)-25s %(levelname)-10s %(module)-20s %(message)s")

# формирование пути
PATH = os.getcwd()
tail = os.path.split(PATH)[1]
if tail == "lesson_2":
    os.chdir("logs/log_files")
    PATH = os.getcwd() + "/server.log"
elif tail == "configs":
    os.chdir(os.pardir)
    os.chdir("log_files")
    PATH = os.getcwd() + "/server.log"

# обработчик записи в файл
HANDLER = logging.handlers.TimedRotatingFileHandler(PATH, encoding="utf-8",
                                                    interval=1,
                                                    when="D")

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
