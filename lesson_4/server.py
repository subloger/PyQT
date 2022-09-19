""" Скрипт серверной части """
import configparser
import json.decoder
import os.path
import sys
import time
from socket import *
import logging
import select
import threading

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from const import CONNECTIONS
from messages_work import incoming_message, send_message
import logs.configs.server_log_config
from decorators import log
from argument_parser import parser_server
from metaclasses import ServerVerifier
from descriptor import ServerPort
from server_storage import ServerStorage
from server_gui import MainWindow, ClientsHistory, Configuration, gui_create_model, create_stat_model


clients_list = []          # список клиентов
messages_for_send = []     # список сообщений для отправки
names = {}                 # словарь с данными клиента

new_connection = False

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
                    except ConnectionRefusedError:
                        LOG.info(f"Клиент {r_client.getpeername()} отключился")
                        print(f"Клиент {r_client.getpeername()} отключился")
                        clients_list.remove(r_client)
                    except json.decoder.JSONDecodeError:
                        print("Получен пустой запрос")

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

            # формируется ответ на сообщение "присутствия"
            if client_message["account_name"] not in names.keys():
                names[client_message["account_name"]] = client
                answer = {"response": 200,
                          "time": f"{time.ctime(time.time())}",
                          "to_user": client_message["account_name"],
                          "alert": "Подтверждение присутствия получено"}
                LOG.info(f"Сформирован ответ - {answer}")
                ip, port = client.getpeername()
                self.database.user_login(client_message["account_name"], ip_address=ip, port=port)
                with threading.Lock():
                    global new_connection
                    new_connection = True
                return answer

            else:
                client_exist = {"response": 400,
                                "time": f"{time.ctime(time.time())}",
                                "error": "Пользователь с таким именем уже существует"}
                return client_exist

        elif client_message["action"] == "contacts":

            # формируется ответ на запросы при работе со списком контактов
            target_client = client_message["contacts"]["sender_user"]
            add_del_client = client_message["contacts"]["target_user"]

            if client_message["contacts"]["action"] == "get_contacts":
                contact_list = self.database.get_contacts(target_client)
                list_contacts = {"response": 202,
                                 "to_user": target_client,
                                 "contacts": contact_list
                                 }
                LOG.info(f"Запрошен список контактов - {list_contacts['contacts']}")
                return list_contacts

            elif client_message["contacts"]["action"] == "add_contact":
                self.database.add_contact(target_client, add_del_client)
                add_answer = {"response": 202,
                              "to_user": target_client,
                              "contacts": f"Пользователь '{add_del_client}' добавлен в список контактов"
                              }
                return add_answer

            elif client_message["contacts"]["action"] == "del_contact":
                self.database.del_contact(target_client, add_del_client)
                del_answer = {"response": 202,
                              "to_user": target_client,
                              "contacts": f"Пользователь '{add_del_client}' удален из списка контактов"
                              }
                return del_answer

            elif client_message["contacts"]["action"] == "users":
                all_users = [user[0] for user in self.database.all_users_list()]
                users_answer = {"response": 202,
                                "to_user": target_client,
                                "contacts": all_users
                                }
                return users_answer

            else:
                error_contacts = {"response": 400,
                                  "to_user": target_client,
                                  "error": "Ошибка работы с контактами"
                                  }
                return error_contacts

        elif client_message["action"] == "load_database":
            target_client = client_message["sender_user"]

            all_users = [user[0] for user in self.database.all_users_list()]
            contact_users = [contact for contact in self.database.get_contacts(target_client)]
            loads = {"response": 202,
                     "to_user": target_client,
                     "load_clients": [all_users, contact_users]
                     }
            return loads

        elif client_message["action"] == "msg":

            # формируется ответ на сообщение другому пользователю
            client_mess = client_message["message"]
            client_name = client_message["sender_user"]
            target_client = client_message["target_user"]

            answer = {"response": 200,
                      "time": f"{time.ctime(time.time())}",
                      "from_user": client_name,
                      "to_user": target_client,
                      "answer": client_mess}
            self.database.process_message(client_name, target_client)
            LOG.info(f"Сформирован ответ - {answer}")
            return answer

        elif client_message["action"] == "quit":

            # выход пользователя
            if client_message["account_name"] in names.keys():
                self.database.exit_user(client_message["account_name"])
                with threading.Lock():
                    new_connection = True
                clients_list.remove(names[client_message["account_name"]])
                names[client_message["account_name"]].close()
                del names[client_message["account_name"]]
                return
            # else:
            #     error_answer = {"response": 400,
            #                     "time": f"{time.ctime(time.time())}",
            #                     "error": "Неправильный запрос"}
            #     LOG.error(f"Неверный запрос на выход - {error_answer}")
            #     return error_answer

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

    # database = ServerStorage()

    # аргументы командной строки
    # listen_address, listen_port = parser_server()

    # Загрузка файла конфигурации сервера
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    # Загрузка параметров командной строки, если нет параметров, то задаём
    # значения по умолчанию.
    listen_address, listen_port = (config['SETTINGS']['Listen_Address'], int(config['SETTINGS']['Default_port']))

    # Инициализация базы данных
    database = ServerStorage(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    server_class = Server(listen_address=listen_address, listen_port=listen_port, database=database)
    server = threading.Thread(target=server_class.init_socket)
    server.daemon = True
    server.start()
    LOG.info(f"Сервер запущен - {server}")

    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    main_window.statusBar().showMessage("Статус: is working ")
    main_window.main_tablet.setModel(gui_create_model(database=database))
    main_window.main_tablet.resizeColumnsToContents()
    main_window.main_tablet.resizeRowsToContents()

    # Функция, обновляющая список подключённых, проверяет флаг подключения, и
    # если надо обновляет список
    def update_connections():
        global new_connection
        if new_connection:
            main_window.main_tablet.setModel(gui_create_model(database=database))
            main_window.main_tablet.resizeColumnsToContents()
            main_window.main_tablet.resizeRowsToContents()
            with threading.Lock():
                new_connection = False

    # Функция, создающая окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = ClientsHistory()
        stat_window.history_table.setModel(create_stat_model(database=database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающая окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = Configuration()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    timer = QTimer()
    timer.timeout.connect(update_connections)
    timer.start(1000)

    main_window.refresh_clients_button.triggered.connect(update_connections)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_button.triggered.connect(server_config)

    server_app.exec_()


if __name__ == '__main__':
    main()
