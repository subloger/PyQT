import dis
from pprint import pprint


class ClientVerifier(type):

    """ Метакласс для проверки клиентской части """

    def __init__(cls, cls_name, bases, cls_dict):
        methods = []
        for func in cls_dict:
            try:
                ret = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    if i.opname == "LOAD_GLOBAL":
                        if i.argval not in methods:
                            methods.append(i.argval)

        for command in ('accept', 'listen', 'socket'):
            if command in methods:
                raise TypeError('В классе обнаружено использование запрещённого метода')

        if 'incoming_message' in methods or 'send_message' in methods:
            pass
        else:
            raise TypeError('Отсутствуют вызовы функций, работающих с сокетами.')
        super().__init__(cls_name, bases, cls_dict)


class ServerVerifier(type):

    def __init__(cls, cls_name, bases, cls_dict):
        methods = []
        methods_2 = []
        attrs = []

        for func in cls_dict:
            try:
                ret = dis.get_instructions(cls_dict[func])
            except TypeError:
                pass
            else:
                for i in ret:
                    print(i)
                    if i.opname == 'LOAD_GLOBAL':
                        if i.argval not in methods:
                            # заполняем список методами, использующимися в функциях класса
                            methods.append(i.argval)
                    elif i.opname == 'LOAD_METHOD':
                        if i.argval not in methods_2:
                            # заполняем список атрибутами, использующимися в функциях класса
                            methods_2.append(i.argval)
                    elif i.opname == 'LOAD_ATTR':
                        if i.argval not in attrs:
                            # заполняем список атрибутами, использующимися в функциях класса
                            attrs.append(i.argval)
        print(20 * '-', 'methods', 20 * '-')
        pprint(methods)
        print(20 * '-', 'methods_2', 20 * '-')
        pprint(methods_2)
        print(20 * '-', 'attrs', 20 * '-')
        pprint(attrs)
        print(50 * '-')
        # Если обнаружено использование недопустимого метода connect, вызываем исключение:
        if 'connect' in methods:
            raise TypeError('Использование метода connect недопустимо в серверном классе')
        # Если сокет не инициализировался константами SOCK_STREAM(TCP) AF_INET(IPv4), тоже исключение.
        if not ('SOCK_STREAM' in methods and 'AF_INET' in methods):
            raise TypeError('Некорректная инициализация сокета.')
        # Обязательно вызываем конструктор предка:
        super().__init__(cls_name, bases, cls_dict)
