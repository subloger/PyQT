import unittest
import time

from client import parsing_message


class TestClient(unittest.TestCase):

    """ Тест-кейс проверки модуля клиентской части """

    msg = {"response": 200, "time": f"{time.ctime(time.time())}", "alert": "Подтверждение присутствия получено"}
    msg1 = {"response": 400, "time": f"{time.ctime(time.time())}", "error": "Неправильный запрос"}

    good_msg = {"Код ответа": msg["response"], "Дата и время": msg["time"], "Сообщение": msg["alert"]}
    bad_msg = {"Код ответа": msg1["response"], "Дата и время": msg1["time"], "Сообщение": msg1["error"]}

    def test_parsing_good(self):
        """ Тест ответа на правильный запрос """
        self.assertEqual(parsing_message({"response": 200,
                                          "time": f"{time.ctime(time.time())}",
                                          "alert": "Подтверждение присутствия получено"}),
                         self.good_msg)

    def test_parsing_bad(self):
        """ Тест ответа на неправильный запрос """
        self.assertEqual(parsing_message({"response": 400,
                                          "time": f"{time.ctime(time.time())}",
                                          "error": "Неправильный запрос"}),
                         self.bad_msg)
