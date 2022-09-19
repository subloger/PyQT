import sys
import logging
import inspect


index = sys.argv[0][48:-3]

# выбор регистратора событий
if index == "server":
    LOGGER_DECORATOR = logging.getLogger("main.server")
else:
    LOGGER_DECORATOR = logging.getLogger("main.client")


def log(func):

    """ Функция - декоратор """

    def wrapper(*args, **kwargs):

        """
        Обертка: позволяет записывать в лог-файл параметры
        вызова оборачиваемой функции
        """

        wrapped_function = func(*args, **kwargs)
        LOGGER_DECORATOR.debug(
            f"Была вызвана функция {func.__name__} с параметрами  {args}, {kwargs}\n"
            f"                                                          Вызов из модуля {func.__module__}\n"
            f"                                                          Вызов из функции {inspect.stack()[1][3]}",
            stacklevel=2)
        return wrapped_function

    return wrapper
