""" Скрипт для работы с клиентской базой данных """

from pprint import pprint

from sqlalchemy import create_engine, Table, Column
from sqlalchemy import Text, Integer, String, MetaData, DateTime
from sqlalchemy.orm import mapper, sessionmaker
import datetime


class ClientStorage:

    class KnownUsers:
        def __init__(self, username):
            self.id = None
            self.username = username

    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.contact = contact

    class MessageHistory:
        def __init__(self, from_user, to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.datetime.now()

    def __init__(self):
        self.client_engine = create_engine("sqlite:///client_db.sqlite",
                                           echo=False,
                                           pool_recycle=7200,
                                           connect_args={"check_same_thread": False}
                                           )
        self.metadata = MetaData()

        users = Table("users", self.metadata,
                      Column("id", Integer, primary_key=True),
                      Column("username", String))

        contacts = Table("Contacts", self.metadata,
                         Column("id", Integer, primary_key=True),
                         Column("name", String, unique=True))

        history = Table("Message_history", self.metadata,
                        Column("id", Integer, primary_key=True),
                        Column("from_user", String),
                        Column("to_user", String),
                        Column("message", Text),
                        Column("date", DateTime))

        self.metadata.create_all(self.client_engine)

        mapper(self.KnownUsers, users)
        mapper(self.Contacts, contacts)
        mapper(self.MessageHistory, history)

        Session = sessionmaker(bind=self.client_engine)
        self.session =Session()

        self.session.query(self.Contacts).delete()
        self.session.commit()

    # Функция добавления контактов
    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    # Функция удаления контакта
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()
        self.session.commit()

    # Функция добавления известных пользователей.
    # Пользователи получаются только с сервера, поэтому таблица очищается.
    def add_users(self, users_list):
        self.session.query(self.KnownUsers).delete()
        for user in users_list:
            user_row = self.KnownUsers(user)
            self.session.add(user_row)
        self.session.commit()

    # Функция сохраняет сообщения
    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    # Функция возвращает контакты
    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    # Функция возвращает список известных пользователей
    def get_users(self):
        return [user[0] for user in self.session.query(self.KnownUsers.username).all()]

    # Функция проверяет наличие пользователя в таблице Известных Пользователей
    def check_user(self, user):
        if self.session.query(self.KnownUsers).filter_by(username=user).count():
            return True
        else:
            return False

    # Функция проверяет наличие пользователя в таблице Контактов
    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    # Функция возвращает историю переписки
    def get_history(self, from_who=None, to_who=None):
        query = self.session.query(self.MessageHistory)
        if from_who:
            query = query.filter_by(from_user=from_who)
        if to_who:
            query = query.filter_by(to_user=to_who)
        return [(history_row.from_user, history_row.to_user, history_row.message, history_row.date)
                for history_row in query.all()]
