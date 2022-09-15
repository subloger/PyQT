""" Скрипт клиентской части """

import logging
import sys
from socket import *
import time
import threading

from const import IP_ADDRESS, PORT
from messages_work import incoming_message, send_message
import logs.configs.client_log_config
from decorators import log
from create_message import message_creator
from argument_parser import parser_client
from metaclasses import ClientVerifier


CLIENT_LOGGER = logging.getLogger("main.client")


class CommandsRequest(metaclass=ClientVerifier):

    def __init__(self, server_socket, user_name):
        self.server_socket = server_socket
        self.user_name = user_name
        super().__init__()

    def commands(self):

        """ Функция запрашивает команды от пользователя для выбора действия """

        print("<  help - основные команды  >")

        while True:
            comm = input("\nВведите команду: ")
            if comm == "mess":
                message_to_send = message_creator(sender=self.user_name)
                send_message(client=self.server_socket, message=message_to_send)
                CLIENT_LOGGER.info(f"Отправлено сообщение серверу - {message_to_send}")

            elif comm == "help":
                print("\nКоманды для работы с мессенджером:")
                print("mess - отправка сообщения")
                print("help - помощь по командам")
                print("exit - выход из программы")
                CLIENT_LOGGER.info("Запрошена команда <HELP>")

            elif comm == "exit":
                exit_message = {"action": "quit",
                                "time": f"{time.ctime(time.time())}",
                                "account_name": self.user_name
                                }
                send_message(client=self.server_socket, message=exit_message)
                time.sleep(0.5)
                CLIENT_LOGGER.info(f"Завершение работы по команде пользователя - {self.user_name}")
                break



def presence_msg(client, user):

    """ Функция формирует и отправляет сообщение о присутствии серверу """

    presence = {"action": "presence",
                "time": f"{time.ctime(time.time())}",
                "account_name": user
                }
    try:
        send_message(client=client, message=presence)
        CLIENT_LOGGER.info(f"Отправлено сообщение серверу - {presence}")
    except OSError as send_error:
        CLIENT_LOGGER.error(f"Сообщение не отправлено - {send_error}")
        print("Сообщение не отправлено!")


class ParsingMessage(metaclass=ClientVerifier):

    def __init__(self, server_socket):
        self.server_socket = server_socket
        super().__init__()

    def parsing(self):

        """ Функция парсит ответ сервера """

        while True:

            message = incoming_message(client=self.server_socket)

            if "alert" in message.keys():
                good_msg = {"Код ответа": message["response"],
                            "Дата и время": message["time"],
                            "Сообщение": message["alert"]
                            }
                CLIENT_LOGGER.info(f"Получен ответ от сервера - {good_msg}")

                if message["response"] == 200:
                    print("Подключение к серверу: OK\n")

            elif "error" in message.keys():
                bad_msg = {"Код ответа": message["response"],
                           "Дата и время": message["time"],
                           "Сообщение": message["error"]
                           }
                CLIENT_LOGGER.error(f"Ошибка запроса к серверу - {bad_msg}")

                for key in bad_msg:
                    print(f"{key}: {bad_msg[key]}")

            elif "answer" in message.keys():
                mess_from_server = {"Дата и время   ": message["time"],
                                    "От             ": message["from_user"],
                                    "Текст сообщения": message["answer"]
                                    }
                CLIENT_LOGGER.info(f"Получено сообщение от пользователя {message['from_user']} - {mess_from_server}")

                print("\n+-------------------------------------------+")
                for num, key in enumerate(mess_from_server, start=1):
                    if num <= 2:
                        length = len(mess_from_server[key])
                        print(f"| {key}: {mess_from_server[key]} {(24 - length) * ' '}|")
                    else:
                        print("+-------------------------------------------+")
                        print(f"  {key}: {mess_from_server[key]}")
                print("+-------------------------------------------+")




def main():

    """ Основная функция клиентской части мессенджера """

    # аргументы командной строки
    ip_address_connect, port_server_connect, client_name = parser_client()

    if client_name:
        print(f"*** КЛИЕНТСКАЯ КОНСОЛЬ ***\n\n   пользователь: {client_name}\n")
    else:
        client_name = input("Введите имя пользователя:  ")
        print(f"*** КЛИЕНТСКАЯ КОНСОЛЬ ***\n\n   пользователь: {client_name}\n")

    ip_address = ''
    port = 0

    # параметр командной строки для ip-адреса
    try:
        if sys.argv[1]:
            ip_address = ip_address_connect  # sys.argv[1]
    except IndexError:
        ip_address = IP_ADDRESS

    # параметр командной строки для порта
    try:
        if sys.argv[2]:
            port_number = port_server_connect  # int(sys.argv[2])
            if 0 < port_number < 1024 and port_number > 65535:
                print("Номер порта может быть в диапазоне от 1024 до 65535")
                CLIENT_LOGGER.critical(f"Номер порта вне диапазона (1024 - 65535) - {port_number}")
                sys.exit()
            else:
                port = port_number
    except IndexError:
        port = int(PORT)

    try:
        soc = socket(AF_INET, SOCK_STREAM)
        CLIENT_LOGGER.info("Создан сокет")
        soc.connect((ip_address, port))
        CLIENT_LOGGER.info("Подключение к серверу")
        presence_msg(client=soc, user=client_name)
    except ConnectionRefusedError as refused_error:
        CLIENT_LOGGER.error(f"Ошибка подключения к серверу - {refused_error}")
    else:

        # запуск процесса прослушивания сервера
        pars_mess = ParsingMessage(server_socket=soc)
        message_reader = threading.Thread(target=pars_mess.parsing)
        message_reader.daemon = True
        message_reader.start()
        CLIENT_LOGGER.info(f"Запущен процесс приема сообщений - {message_reader}")

        # запуск процесса отправки сообщений
        comm_req = CommandsRequest(server_socket=soc, user_name=client_name)
        message_sender = threading.Thread(target=comm_req.commands)
        message_sender.daemon = True
        message_sender.start()
        CLIENT_LOGGER.info(f"Запущен процесс отправки сообщений - {message_sender, }")

        while True:
            time.sleep(1)
            if message_reader.is_alive() and message_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
