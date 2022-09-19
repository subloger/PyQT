""" Скрипт для работы с базой данных сервера """
import os
from pprint import pprint

from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, DateTime, ForeignKey
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class ServerStorage:

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

    class UsersLogin:
        def __init__(self, name, ip_address, port):
            self.id = None
            self.name = name
            self.time_connect = datetime.datetime.now()
            self.ip_address = ip_address
            self.port = port

    class UsersContact:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    class UsersMessages:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    def __init__(self, path):
        self.server_engine = create_engine(f"sqlite:///{path}",
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

        # таблица истории входов
        users_login = Table("Users_login", self.metadata,
                            Column("id", Integer, primary_key=True),
                            Column("name", ForeignKey("All_users.name")),
                            Column("time_connect", DateTime),
                            Column("ip_address", String),
                            Column("port", Integer))

        # таблица контактов пользователей
        users_contacts = Table("Users_contacts", self.metadata,
                               Column("id", Integer, primary_key=True),
                               Column("user", ForeignKey("All_users.id")),
                               Column("contact", ForeignKey("All_users.id")))

        # таблица принятых и отправленных сообщений
        users_messages = Table("Users_message", self.metadata,
                               Column("id", Integer, primary_key=True),
                               Column("user", ForeignKey("All_users.id")),
                               Column("sent", Integer),
                               Column("accepted", Integer))

        # создание таблиц
        self.metadata.create_all(self.server_engine)

        mapper(self.AllUsers, all_users)
        mapper(self.ActiveUsers, active_users)
        mapper(self.UsersLogin, users_login)
        mapper(self.UsersContact, users_contacts)
        mapper(self.UsersMessages, users_messages)

        Session = sessionmaker(bind=self.server_engine)
        self.session = Session()

        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

    def user_login(self, username, ip_address, port):

        """ Метод регистрирующий подключение новых пользователей """

        print(f"Подключился клиент '{username}' - {ip_address}: {port}")

        user = self.session.query(self.AllUsers).filter_by(name=username)

        # проверка на нового пользователя
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
        new_user_history = self.UsersLogin(username, ip_address, port)
        self.session.add(new_user_history)
        self.session.commit()

    def exit_user(self, username):

        """ Метод регистрирующий отключение клиентов """

        print(f"Клиент '{username}' отключился")

        user = self.session.query(self.AllUsers).filter_by(name=username).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.commit()

    def all_users_list(self):

        """ Метод возвращающий список всех клиентов """

        users = self.session.query(self.AllUsers.name, self.AllUsers.last_activities)
        return users.all()

    def active_user_list(self):


        """ Метод возвращающий список активных пользователей """

        active_users = self.session.query(self.AllUsers.name,
                                          self.ActiveUsers.ip_address,
                                          self.ActiveUsers.port,
                                          self.ActiveUsers.time_connect).join(self.AllUsers)

        return active_users.all()

    def users_history(self, username=None):

        """ Метод возвращающий список историю подключения пользователей """

        users_history = self.session.query(self.AllUsers.name,
                                           self.UsersLogin.time_connect,
                                           self.UsersLogin.ip_address,
                                           self.UsersLogin.port).join(self.AllUsers)

        if username:
            user_history = users_history.filter(self.AllUsers.name == username)
            return user_history.all()
        return users_history.all()

    def process_message(self, sender, recipient):

        """ Метод фиксирует передачу сообщений и записывает их количество в базу данных"""

        send = self.session.query(self.AllUsers).filter_by(name=sender).first().id
        recip = self.session.query(self.AllUsers).filter_by(name=recipient).first().id

        sender_row = self.session.query(self.UsersMessages).filter_by(user=send).first()
        if sender_row is None:
            sender_row = self.UsersMessages(send)
            self.session.add(sender_row)
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersMessages).filter_by(user=recip).first()
        if recipient_row is None:
            recipient_row = self.UsersMessages(recip)
            self.session.add(recipient_row)
        recipient_row.accepted += 1

        self.session.commit()

    def add_contact(self, user, contact):

        """ Метод добавляет контакт в список контактов для пользователя """

        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact or self.session.query(self.UsersContact).filter_by(user=user.id, contact=contact.id).count():
            return

        contact_row = self.UsersContact(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()

    def del_contact(self, user, contact):

        """ Метод удаляет контакт из списка контактов для пользователя """

        user = self.session.query(self.AllUsers).filter_by(name=user).first()
        contact = self.session.query(self.AllUsers).filter_by(name=contact).first()

        if not contact:
            return

        # print(self.session.query(self.UsersContact).filter(self.UsersContact.user == user.id,
        #                                                    self.UsersContact.contact == contact.id
        #                                                    ).delete())
        self.session.query(self.UsersContact).filter(self.UsersContact.user == user.id,
                                                     self.UsersContact.contact == contact.id
                                                     ).delete()

        self.session.commit()

    def get_contacts(self, username):

        """ Метод возвращает список контактов пользователя """

        user = self.session.query(self.AllUsers).filter_by(name=username).one()

        query = self.session.query(self.UsersContact,
                                   self.AllUsers.name).filter_by(
            user=user.id).join(self.AllUsers,
                               self.UsersContact.contact == self.AllUsers.id)

        return [contact[1] for contact in query.all()]

    def message_history(self):
        query = self.session.query(self.AllUsers.name,
                                   self.AllUsers.last_activities,
                                   self.UsersMessages.sent,
                                   self.UsersMessages.accepted).join(self.AllUsers)

        return query.all()


if __name__ == "__main__":
    test_db = ServerStorage()
    test_db.user_login('1111', '192.168.1.113', 8080)
    test_db.user_login('McG2', '192.168.1.113', 8081)
    pprint(test_db.active_user_list())
    test_db.exit_user('McG2')
    pprint(test_db.users_history())
    test_db.add_contact('test2', 'test1')
    test_db.add_contact('test1', 'test3')
    test_db.add_contact('test1', 'test6')
    test_db.del_contact('test1', 'test3')
    test_db.process_message('McG2', '1111')
    pprint(test_db.message_history())
