""" Скрипт серверной части """
import json.decoder
import os.path
import time
from socket import *
import logging
import select
import threading

from const import CONNECTIONS
from messages_work import incoming_message, send_message
import logs.configs.server_log_config
from decorators import log
from argument_parser import parser_server
from metaclasses import ServerVerifier
from descriptor import ServerPort
from storage import ServerStorage


clients_list = []          # список клиентов
messages_for_send = []     # список сообщений для отправки
names = {}                 # словарь с данными клиента


LOG = logging.getLogger("main.server")


class Server(metaclass=ServerVerifier):
    listen_port = ServerPort()

    def __init__(self, listen_address, listen_port, database):
        self.listen_address = listen_address
        self.listen_port = listen_port
        self.database = database
        super().__init__()

    def init_socket(self):
        soc = socket(AF_INET, SOCK_STREAM)
        soc.bind((self.listen_address, self.listen_port))
        soc.listen(CONNECTIONS)
        soc.settimeout(0.5)

        writes_clients = []        # клиенты ожидающие чтения
        reads_clients = []         # клиенты ожидающие записи
        errors_clients = []

        while True:

            try:
                client, addr = soc.accept()
                LOG.info(f"Получен запрос на соединение от {str(addr)}")
                # print(f"Подключился клиент - {addr}")
            except OSError:
                pass
            else:
                clients_list.append(client)

            if clients_list:
                reads_clients, writes_clients, errors_clients = select.select(clients_list,
                                                                              clients_list,
                                                                              [])

            if reads_clients:
                for r_client in reads_clients:

                    try:
                        client_data = incoming_message(client=r_client)
                        LOG.info(f"Получено сообщение от клиента - {client_data}")
                        response = self.response_message(client_message=client_data, client=r_client)
                        if response is not None:
                            messages_for_send.append(response)
                        else:
                            print(f"Клиент отключился")
                    except ConnectionRefusedError:
                        LOG.info(f"Клиент {r_client.getpeername()} отключился")
                        print(f"Клиент {r_client.getpeername()} отключился")
                        clients_list.remove(r_client)
                    # except json.decoder.JSONDecodeError:
                    #     print("Получен пустой запрос")

            for mess in messages_for_send:
                try:
                    self.checking_message(messages=mess, names_clients=names, awaiting_clients=writes_clients)
                except ConnectionRefusedError:
                    LOG.info(f"Клиент {mess['to_user']} отключился")
                    print(f"Клиент {names[mess['to_user']]} отключился")
                    clients_list.remove(names[mess["to_user"]])
            messages_for_send.clear()

    def response_message(self, client_message, client):

        """ Функция формирует ответ сервера """

        if client_message["action"] == "presence":
            if client_message["account_name"] not in names.keys():
                names[client_message["account_name"]] = client
                answer = {"response": 200,
                          "time": f"{time.ctime(time.time())}",
                          "to_user": client_message["account_name"],
                          "alert": "Подтверждение присутствия получено"}
                LOG.info(f"Сформирован ответ - {answer}")
                ip, port = client.getpeername()
                self.database.user_login(client_message["account_name"], ip_address=ip, port=port)
                return answer

            else:
                client_exist = {"response": 400,
                                "time": f"{time.ctime(time.time())}",
                                "error": "Пользователь с таким именем уже существует"}
                return client_exist

        elif client_message["action"] == "probe":
            pass
        elif client_message["action"] == "msg":

            client_mess = client_message["message"]
            client_name = client_message["sender_user"]
            target_client = client_message["target_user"]

            answer = {"response": 200,
                      "time": f"{time.ctime(time.time())}",
                      "from_user": client_name,
                      "to_user": target_client,
                      "answer": client_mess}
            LOG.info(f"Сформирован ответ - {answer}")
            return answer

        elif client_message["action"] == "quit":

            if client_message["account_name"] in names.keys():
                self.database.exit_user(client_message["account_name"])
                clients_list.remove(names[client_message["account_name"]])
                names[client_message["account_name"]].close()
                del names[client_message["account_name"]]
                return
            else:
                error_answer = {"response": 400,
                                "time": f"{time.ctime(time.time())}",
                                "error": "Неправильный запрос"}
                LOG.error(f"Неверный запрос на выход - {error_answer}")
                return error_answer

        elif client_message["action"] == "authenticate":
            pass
        elif client_message["action"] == "join":
            pass
        elif client_message["action"] == "leave":
            pass
        else:
            return {"response": 400,
                    "time": f"{time.ctime(time.time())}",
                    "error": "Неправильный запрос"}
            LOG.error(f"Неправильный формат запроса - {client_message}")

    def checking_message(self, messages, names_clients, awaiting_clients):

        """ Функция проверяет наличие параметров для отправки сообщения """

        if messages["to_user"] in names_clients.keys() and names_clients.get(messages["to_user"]) in awaiting_clients:
            send_message(client=names_clients[messages["to_user"]], message=messages)
            LOG.info(f"Отправлен ответ - {names_clients[messages['to_user']].getpeername()} - {messages}")


def main():

    database = ServerStorage()

    # аргументы командной строки
    listen_address, listen_port = parser_server()

    server_class = Server(listen_address=listen_address, listen_port=listen_port, database=database)
    server = threading.Thread(target=server_class.init_socket)
    server.daemon = True
    server.start()
    LOG.info(f"Сервер запущен - {server}")

    def help_list():
        print("\n      *** Поддерживаемые команды: ***\n")
        print("users - список всех пользователей")
        print("active - подключённые пользователи")
        print("history - история подключения пользователей")
        print("exit - завершение работы сервера")
        print("help - вывод справки\n")

    help_list()

    while True:
        command = input("Введите команду:  ")
        if command == "users":
            users = sorted(database.all_users_list())
            if users:
                for user in users:
                    print(f"\nПользователь {user[0]}, последний вход {user[1]}")
                print()
            else:
                print("Пользователей не зарегистрировано!")
        elif command == "active":
            active_users = sorted(database.active_user_list())
            if active_users:
                for user in active_users:
                    print(f"Пользователь {user[0]}, подключен: {user[1]}:{user[2]}, "
                          f"время установки соединения: {user[3]}")
            else:
                print("Нет подключенных пользователей!")
        elif command == "history":
            name = input("Введите имя пользователя или нажмите Enter:  ")
            history = sorted(database.users_history(name))
            if history:
                print("----------------------------------------")
                for user in sorted(database.users_history(name)):
                    print(f" Пользователь: '{user[0]}'\n"
                          f" Время входа: {user[1]}\n"
                          f" Вход с: {user[2]}: {user[3]}\n"
                          f"----------------------------------------")
            else:
                print("Нет истории подключений!")
        elif command == "exit":
            break
        elif command == "help":
            help_list()
        else:
            print("Команда не распознана!")


if __name__ == '__main__':
    main()
