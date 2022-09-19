""" Скрипт работы с сообщениями """

import time
import logging

CLIENT_LOGGER = logging.getLogger("main.client")


def message_creator(sender):

    """
    Функция запрашивает данные для формирования сообщение для отправки
    """

    to_user = input("Введите получателя сообщения:  ")
    mess = input("Введите сообщение:  ")

    message_from_client = {"action": "msg",
                           "time": f"{time.ctime(time.time())}",
                           "target_user": to_user,
                           "sender_user": sender,
                           "message": mess}

    return message_from_client
