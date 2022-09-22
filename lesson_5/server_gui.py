
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolTip, QAction, qApp, QTableView, QLabel, QDialog, \
    QPushButton, QLineEdit, QFileDialog
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem


# GUI - Создание таблицы QModel, для отображения в окне программы.
def gui_create_model(database):
    list_users = database.active_user_list()
    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])
    for row in list_users:
        print(row)
        user, ip, port, time = row
        user = QStandardItem(user)
        user.setEditable(False)
        ip = QStandardItem(ip)
        ip.setEditable(False)
        port = QStandardItem(str(port))
        port.setEditable(False)
        # Уберём миллисекунды из строки времени, т.к. такая точность не требуется.
        time = QStandardItem(str(time.replace(microsecond=0)))
        time.setEditable(False)
        list_table.appendRow([user, ip, port, time])
    return list_table


# GUI - Функция реализующая заполнение таблицы историей сообщений.
def create_stat_model(database):
    # Список записей из базы
    hist_list = database.message_history()

    # Объект модели данных:
    list_table = QStandardItemModel()
    list_table.setHorizontalHeaderLabels(
        ['Имя Клиента', 'Последний раз входил', 'Сообщений отправлено', 'Сообщений получено'])
    for row in hist_list:
        user, last_seen, sent, recvd = row
        user = QStandardItem(user)
        user.setEditable(False)
        last_seen = QStandardItem(str(last_seen.replace(microsecond=0)))
        last_seen.setEditable(False)
        sent = QStandardItem(str(sent))
        sent.setEditable(False)
        recvd = QStandardItem(str(recvd))
        recvd.setEditable(False)
        list_table.appendRow([user, last_seen, sent, recvd])
    return list_table


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        QToolTip.setFont(QFont("SansSerif", 10))

        # кнопка закрытия приложения
        self.exit_button = QAction("Выход", self)
        self.exit_button.setShortcut("Ctrl+Q")
        self.exit_button.setToolTip("Выход")
        self.exit_button.triggered.connect(qApp.quit)

        # кнопка обновления списка клиентов
        self.refresh_clients_button = QAction("Обновить список", self)

        # кнопка для вывода истории сообщений
        self.show_history_button = QAction("История клиентов", self)

        # кнопка настроек сервера
        self.config_button = QAction("Настройки сервера", self)

        self.toolbar = self.addToolBar("Main")
        self.toolbar.addAction(self.exit_button)
        self.toolbar.addAction(self.refresh_clients_button)
        self.toolbar.addAction(self.show_history_button)
        self.toolbar.addAction(self.config_button)

        self.label = QLabel("-- Список подключенных клиентов --", self)
        self.label.move(270, 35)
        self.label.setFixedSize(400, 30)

        # таблица для вывода данных
        self.main_tablet = QTableView(self)
        self.main_tablet.move(10, 60)
        self.main_tablet.setFixedSize(780, 400)

        self.statusBar()

        self.setWindowTitle("Сервер - Основной модуль")
        self.setFixedSize(800, 500)
        self.show()


class ClientsHistory(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Настройки окна:
        self.setWindowTitle('Статистика клиентов')
        self.setFixedSize(600, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(250, 650)
        self.close_button.clicked.connect(self.close)

        # Лист с историей
        self.history_table = QTableView(self)
        self.history_table.move(10, 10)
        self.history_table.setFixedSize(580, 620)

        self.show()


class Configuration(QDialog):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Настройки окна
        self.setFixedSize(450, 260)
        self.setWindowTitle('Настройки сервера')

        # Надпись о файле базы данных:
        self.db_path_label = QLabel('Путь до файла базы данных: ', self)
        self.db_path_label.move(10, 10)
        self.db_path_label.setFixedSize(250, 15)

        # Строка с путём базы
        self.db_path = QLineEdit(self)
        self.db_path.setFixedSize(300, 20)
        self.db_path.move(10, 30)
        self.db_path.setReadOnly(True)

        # Кнопка выбора пути.
        self.db_path_select = QPushButton('Обзор...', self)
        self.db_path_select.move(350, 28)

        # Функция обработчик открытия окна выбора папки
        def open_file_dialog():
            global dialog
            dialog = QFileDialog(self)
            path = dialog.getExistingDirectory()
            path = path.replace('/', '\\')
            self.db_path.insert(path)

        self.db_path_select.clicked.connect(open_file_dialog)

        # Метка с именем поля файла базы данных
        db_file_label = QLabel('Имя файла базы данных: ', self)
        db_file_label.move(10, 68)
        db_file_label.setFixedSize(180, 15)

        # Поле для ввода имени файла
        self.db_file = QLineEdit(self)
        self.db_file.move(280, 66)
        self.db_file.setFixedSize(150, 20)

        # Метка с номером порта
        self.port_label = QLabel('Номер порта для соединений:', self)
        self.port_label.move(10, 108)
        self.port_label.setFixedSize(215, 15)

        # Поле для ввода номера порта
        self.port = QLineEdit(self)
        self.port.move(280, 108)
        self.port.setFixedSize(150, 20)

        # Метка с адресом для соединений
        self.ip_label = QLabel('С какого IP принимаем соединения:', self)
        self.ip_label.move(10, 148)
        self.ip_label.setFixedSize(255, 15)

        # Метка с напоминанием о пустом поле.
        self.ip_label_note = QLabel(' оставьте это поле пустым, чтобы\n принимать соединения с любых адресов.', self)
        self.ip_label_note.move(10, 168)
        self.ip_label_note.setFixedSize(500, 30)

        # Поле для ввода ip
        self.ip = QLineEdit(self)
        self.ip.move(280, 148)
        self.ip.setFixedSize(150, 20)

        # Кнопка сохранения настроек
        self.save_btn = QPushButton('Сохранить', self)
        self.save_btn.move(260, 220)

        # Кнопка закрытия окна
        self.close_button = QPushButton('Закрыть', self)
        self.close_button.move(350, 220)
        self.close_button.clicked.connect(self.close)

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.statusBar().showMessage("Тестовый запуск программы")
    test_list = QStandardItemModel(main_window)
    test_list.setHorizontalHeaderLabels(['Имя Клиента', 'IP Адрес', 'Порт', 'Время подключения'])

    test_list.appendRow([QStandardItem('test1'), QStandardItem('192.198.0.5'),
                         QStandardItem('23544'), QStandardItem('16:20:34')])
    test_list.appendRow([QStandardItem('test2'), QStandardItem('192.198.0.8'),
                         QStandardItem('33245'), QStandardItem('16:22:11')])

    # win = ClientsHistory()

    # window = Configuration()

    sys.exit(app.exec_())
