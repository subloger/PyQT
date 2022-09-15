""" Скрипт для работы с базой данных """
import os

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, DateTime, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class ServerStorage:

    def __init__(self):

        self.engine = create_engine("sqlite:///server_db.sqlite",
                                    echo=False,
                                    pool_recycle=7200,
                                    connect_args={"check_same_thread": False}
                                    )

        self.metadata = MetaData()

        # таблица содержащая всех пользователей
        all_users = Table("All_users", self.metadata,
                          Column("id", Integer, primary_key=True),
                          Column("name", String),
                          Column("last_activities", DateTime))

        # таблица содержащая пользователей подключенных в данный момент
        active_users = Table("Active_users", self.metadata,
                             Column("id", Integer, primary_key=True),
                             Column("user", ForeignKey("All_users.id"), unique=True),
                             Column("time_connect", DateTime),
                             Column("ip_address", String),
                             Column("port", Integer))

        # таблица истории пользователя
        user_history = Table("User_history", self.metadata,
                             Column("id", Integer, primary_key=True),
                             Column("name", ForeignKey("All_users.name")),
                             Column("time_connect", DateTime),
                             Column("ip_address", String),
                             Column("port", Integer))

        # создание таблиц
        self.metadata.create_all(self.engine)

        mapper(self.AllUsers, all_users)
        mapper(self.ActiveUsers, active_users)
        mapper(self.UserHistory, user_history)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    class AllUsers:
        def __init__(self, name, last_activities):
            self.id = None
            self.name = name
            self.last_activities = last_activities

    class ActiveUsers:
        def __init__(self, user, ip_address, port):
            self.id = None
            self.user = user
            self.time_connect = datetime.datetime.now()
            self.ip_address = ip_address
            self.port = port

    class UserHistory:
        def __init__(self, name, ip_address, port):
            self.id = None
            self.name = name
            self.time_connect = datetime.datetime.now()
            self.ip_address = ip_address
            self.port = port

    # функция регистрирующая подключение новых пользователей
    def user_login(self, username, ip_address, port):
        print(f"Подключился клиент - {ip_address}: {port}")

        user = self.session.query(self.AllUsers).filter_by(name=username)

        if user.count():
            u = user.first()
            u.last_activities = datetime.datetime.now()
        else:
            user = self.AllUsers(username, datetime.datetime.now())
            self.session.add(user)
            self.session.commit()

        # добавление нового пользователя в таблицу активных пользователей
        new_active_user = self.ActiveUsers(username, ip_address, port)
        self.session.add(new_active_user)
        self.session.commit()

        # добавление новой записи в таблицу истории подключений
        new_user_history = self.UserHistory(username, ip_address, port)
        self.session.add(new_user_history)
        self.session.commit()

    def exit_user(self, username):
        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def all_users_list(self):
        users = self.session.query(self.AllUsers.name, self.AllUsers.last_activities)
        return users.all()

    def active_user_list(self):
        active_users = self.session.query(self.AllUsers.name,
                                          self.ActiveUsers.time_connect,
                                          self.ActiveUsers.ip_address,
                                          self.ActiveUsers.port).join(self.AllUsers)
        return active_users.all()

    def users_history(self, username=None):
        users_history = self.session.query(self.AllUsers.name,
                                           self.UserHistory.time_connect,
                                           self.UserHistory.ip_address,
                                           self.UserHistory.port).join(self.AllUsers)

        if username:
            user_history = users_history.filter(self.AllUsers.name == username)
            return user_history.all()
        return users_history.all()


if __name__ == "__main__":
    # pass
    test_db = ServerStorage()
    # Выполняем "подключение" пользователя
    test_db.user_login('client_1', '192.168.1.4', 8080)
    test_db.user_login('client_2', '192.168.1.5', 7777)

    # Выводим список кортежей - активных пользователей
    print(' ---- test_db.active_users_list() ----')
    print(test_db.active_user_list())

    # Выполняем "отключение" пользователя
    test_db.exit_user('client_1')
    # И выводим список активных пользователей
    print(' ---- test_db.active_users_list() after logout client_1 ----')
    print(test_db.active_user_list())

    # Запрашиваем историю входов по пользователю
    print(' ---- test_db.login_history(client_1) ----')
    print(test_db.users_history('client_1'))

    # и выводим список известных пользователей
    print(' ---- test_db.users_list() ----')
    print(test_db.all_users_list())
