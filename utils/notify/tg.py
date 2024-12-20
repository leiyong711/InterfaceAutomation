#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @project name: mc_aggregator_pyauto
# @Time   : 2024/12/20 11:00
# @Author  : leo

import time
import requests
from utils import config
from utils.logging_tool.log_control import ERROR


class TgApi:
    def __init__(self):
        self.token = config.tg.token
        self.url = 'https://api.telegram.org/bot' + self.token + '/'

    def post(self, data, url):
        try:
            response = requests.post(url, data)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            ERROR.logger.error(f"Send Telegram HTTP Error: {errh}")
            return None
        except requests.exceptions.ConnectionError as errc:
            ERROR.logger.error(f"Send Telegram Error Connecting: {errc}")
            return None
        except requests.exceptions.Timeout as errt:
            ERROR.logger.error(f"Send Telegram Timeout Error: {errt}")
            return None
        except requests.exceptions.RequestException as err:
            ERROR.logger.error(f"Send Telegram Something Else: {err}")
            return None

        json_response = response.json()
        if not json_response['ok']:
            ERROR.logger.error(f"Send Telegram API returned error: {json_response['error_code']}, {json_response['description']}")
            return None

        return json_response['result']

    def setWebhook(self, url):
        url = self.url + 'setWebhook'
        return self.post({'url': url}, url)

    def split_message(self, message, max_length=4090):
        """拆分发送"""
        return [message[i:i + max_length] for i in range(0, len(message), max_length)]

    def sendMessage(self, msgtext, chat_id, parse_mode="HTML"):
        # 非日常巡检，不发送tg消息
        if config.execution_type != 1:
            return
        url = self.url + 'sendMessage'
        for msg in self.split_message(msgtext, 4095):
            self.post({
                'parse_mode': parse_mode,
                'chat_id': chat_id,
                "text": msg
            }, url)


