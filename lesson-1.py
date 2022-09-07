import platform
import threading
from subprocess import Popen
from subprocess import PIPE
import time
import ipaddress

import tabulate


def list_address(addr_list):

    """ Функция генерирует список IP адресов """

    list_urls = []   # список адресов

    for j in range(len(addr_list)):
        try:
            adr = ipaddress.ip_address(addr_list[j])
            list_urls.append(adr)
        except ValueError:
            list_urls.append(addr_list[j])

    return list_urls


def host_ping(urls_list):

    """ Функция проверяет доступность IP адреса """

    avaliables_hosts = {'Узел доступен': ''}
    not_avaliables_hosts = {'Узел не доступен': ''}

    def processing(url):

        """ Функция пингует адрес """

        if platform.system().lower() == 'windows':
            param = '-n'
        else:
            param = '-c'

        command = ['ping', param, '2', url]

        process = Popen(command, stdout=PIPE, stderr=PIPE)

        lock = threading.Lock()
        if process.wait() == 0:
            with lock:
                avaliables_hosts['Узел доступен'] += f'{url}\n'
        else:
            with lock:
                not_avaliables_hosts['Узел не доступен'] += f'{url}\n'

    threads = []
    for i in urls_list:
        TRH = threading.Thread(target=processing, args=(str(i),))
        TRH.daemon = True
        TRH.start()
        threads.append(TRH)

    for thread in threads:
        thread.join()

    return [avaliables_hosts, not_avaliables_hosts]


def host_range_ping():

    """ Функция проверяет адреса из заданного диапазона """

    list_for_checking = []
    while True:
        address = input('Введите проверяемый адрес:  ')
        try:
            ipv4 = ipaddress.ip_address(address)
            break
        except ValueError as error:
            print(error)
            print('\n*** Введите адрес в формате 000.000.000.000 ***\n')
            continue

    while True:
        range_value = input('Введите проверяемый диапазон адресов последнего октета:  ')
        address_count = 256 - int(str(ipv4).split('.')[3])
        if range_value.isalpha():
            print('\n*** Укажите числовое значение ***\n')
        elif int(range_value) > address_count:
            print(f'\n*** При заданном адресе значение не может быть больше {address_count} ***\n')
        else:
            break

    for i in range(int(range_value)):
        list_for_checking.append(ipv4 + i)

    return list_for_checking


def host_range_ping_tab(data_list):

    """ Функция формирует вывод данных в виде таблицы """

    print('\n========================================')
    print(tabulate.tabulate(data_list, headers='keys', tablefmt='pipe', stralign='center'))
    print('========================================\n')


if __name__ == '__main__':

    start = time.time()

    hosts_list = host_range_ping()
    addr = list_address(addr_list=hosts_list)
    host_range_ping_tab(host_ping(urls_list=addr))

    end = time.time()
    print(f'\nВремя выполнения скрипта - {round(end - start, 2)} сек')
