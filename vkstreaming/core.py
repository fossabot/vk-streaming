# -*- coding: utf-8 -*-
"""
@author: Daniil Suvorov
@contact: https://severecloud.me
"""

import json
import requests
import websocket


"""
максимальное количество правил — 10;
максимальное количество ключевых слов в правиле — 10;
максимальный размер правила в байтах — 4096;
максимальный размер метки правила (tag) в байтах — 256;
"""
MAX_RULES = 10
MAX_WORD_RULES = 10


class Streaming(object):
    """Класс"""
    def __init__(self, endpoint=None, key=None):
        """
        :param endpoint: Хост для подключения к серверу
        :param key: Ключ доступа
        """
        self.endpoint = endpoint
        self.key = key
        self.list_func = []
        self.ws = ''

    def get_rules(self):
        """Получение правил"""

        url = "https://{}/rules?key={}".format(self.endpoint, self.key)

        response = requests.get(url).json()

        if response['code'] != 200:
            raise VkError(response['error']['error_code'],
                          response['error']['message'])
        else:
            return response['rules']

    def add_rules(self, tag, value):
        """
        :param tag: Метка правила
        :param value: Cтроковое представление правила
        """

        url = "https://{}/rules?key={}".format(self.endpoint, self.key)
        values = {"rule": {"value": value, "tag": tag}}

        response = requests.post(url, json=values).json()

        if response['code'] != 200:
            raise VkError(response['error']['error_code'],
                          response['error']['message'])

    def del_rules(self, tag):
        """
        :param tag: Метка правила
        """

        url = "https://{}/rules?key={}".format(self.endpoint, self.key)
        values = {"tag": tag}

        response = requests.delete(url, json=values).json()

        if response['code'] != 200:
            raise VkError(response['error']['error_code'],
                          response['error']['message'])

    def del_all_rules(self):
        """Удалить все правила"""
        rules = self.get_rules()
        if rules:
            for item in rules:
                self.del_rules(item['tag'])

    def update_rules(self, array):
        """
        :param array: Массив правил
        """
        if len(array) > MAX_RULES:
            raise VkError(2006, "Too many rules")
        else:
            self.del_all_rules()
            for item in array:
                self.add_rules(item['tag'], item['value'])

    def stream(self, func):
        """Декоратор"""
        self.list_func.append(func)

    def start(self):
        """Запустить стрим"""

        def on_message(ws, message):
            """WebSocket получаем сообщение"""
            message = json.loads(message)
            if message['code'] == 100:
                for func in self.list_func:
                    func(message['event'])
            else:
                ws.close()
                self.start()

        def on_error(ws, error):
            """WebSocket получаем ошибку"""
            raise VkError(0, error)

        def on_close(ws):
            """WebSocket закрыт"""
            pass

        url = "wss://{}/stream?key={}".format(self.endpoint, self.key)
        self.ws = websocket.WebSocketApp(url,
                                         on_message=on_message,
                                         on_error=on_error,
                                         on_close=on_close)
        self.ws.run_forever()

    def stop(self):
        """Остановить стрим"""
        self.ws.close()


class VkError(Exception):
    """Ошибка vk"""
    def __init__(self, error_code, message):
        """
        :param error_code: Код ошибки
        :param message: Сообщение
        """
        self.message, self.error_code = message, error_code

    def __str__(self):
        return "{}: {}".format(self.error_code, self.message)