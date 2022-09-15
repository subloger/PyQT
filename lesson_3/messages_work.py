""" Скрипт работы с сообщениями """

import json

from const import PACK, ENCODING


def incoming_message(client):

    """ Функция принимает сообщение и декодирует его """

    data = client.recv(PACK)
    data_decode = data.decode(ENCODING)
    data_decode = json.loads(data_decode)
    return data_decode


def send_message(client, message):

    """ Функция отправляет ответное сообщение """

    msg = message
    msg_to_send = json.dumps(msg)
    client.send(msg_to_send.encode(ENCODING))
