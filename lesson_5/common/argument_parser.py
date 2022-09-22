""" Скрипт для парсинга аргументов командной строки """

import argparse
import sys

from lesson_5.common.const import IP_ADDRESS, PORT


def parser_server():

    """ Парсер аргументов командной строки серверной части """

    parser = argparse.ArgumentParser()
    parser.add_argument('-a', default=IP_ADDRESS, nargs='?')
    parser.add_argument('-p', default=PORT, type=int, nargs='?')
    list_argument_server = parser.parse_args(sys.argv[1:])
    listen_address = list_argument_server.a
    listen_port = list_argument_server.p

    return listen_address, listen_port


def parser_client():

    """ Парсер аргументов командной строки клиентской части """

    cmd_parser = argparse.ArgumentParser(description="Парсинг командной строки")
    cmd_parser.add_argument("ip_addr", type=str, help="Введите IP-адрес", default=IP_ADDRESS, nargs="?")
    cmd_parser.add_argument("port", type=int, help="Введите номер порта", default=PORT, nargs="?")
    cmd_parser.add_argument("-n", "--name", type=str, help="Имя клиента", default=None, nargs="?")
    list_arguments_client = cmd_parser.parse_args()
    ip_address_connect = list_arguments_client.ip_addr
    port_server_connect = list_arguments_client.port
    client_name = list_arguments_client.name

    return ip_address_connect, port_server_connect, client_name


