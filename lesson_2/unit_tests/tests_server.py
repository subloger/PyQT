import unittest
import time


from server import response_message


class TestServer(unittest.TestCase):

    """ Тест-кейс проверки модуля серверной части """

    good_answer = {"response": 200,
                   "time": f"{time.ctime(time.time())}",
                   "alert": "Подтверждение присутствия получено"}

    bad_answer = {"response": 400,
                  "time": f"{time.ctime(time.time())}",
                  "error": "Неправильный запрос"}

    def test_presence(self):
        """ Тест соответствия правильному запросу """
        self.assertEqual(response_message({"action": "presence",
                                           "time": f"{time.ctime(time.time())}",
                                           "user": {"account_name": "USERNAME",
                                                    "status": "Yep, I am here!"}
                                           }), self.good_answer, print("<test_presence> - пройден"))

    def test_time(self):
        """ Тест наличия значения времени в запросе """
        self.assertEqual(response_message({"action": "presence",
                                           "user": {"account_name": "USERNAME",
                                                    "status": "Yep, I am here!"}
                                           }), self.bad_answer, print("<test_time> - пройден"))

    def test_user(self):
        """ Тест на правильность имени пользователя """
        self.assertEqual(response_message({"action": "presence",
                                           "time": f"{time.ctime(time.time())}",
                                           "user": {"account_name": "unknowed",
                                                    "status": "Yep, I am here!"}
                                           }), self.bad_answer, print("<test_user> - пройден"))


if __name__ == "__main__":
    unittest.main()
