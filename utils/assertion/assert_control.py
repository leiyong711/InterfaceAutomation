#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @project name: mc_aggregator_pyauto
# @Time   : 2024/12/20 10:54
# @Author  : leo

"""
断言类型封装，支持json响应断言、数据库断言
"""

import ast
import json
import time
from typing import Text, Dict, Any, Union
from jsonpath import jsonpath
from utils.other_tools.models import AssertMethod
from utils.logging_tool.log_control import ERROR, WARNING
from utils.read_files_tools.regular_control import cache_regular
from utils.other_tools.models import load_module_functions
from utils.assertion import assert_type
from utils.other_tools.exceptions import JsonpathExtractionFailed, SqlNotFound, AssertTypeError
from utils import config
from utils.logging_tool.log_control import INFO, ERROR
from utils.notify.tg import TgApi

tg = TgApi()


class Assert:
    """ assert 模块封装 """

    def __init__(self, assert_data: Dict):
        self.assert_data = ast.literal_eval(cache_regular(str(assert_data)))
        self.functions_mapping = load_module_functions(assert_type)

    @staticmethod
    def _check_params(
            response_data: Text,
            sql_data: Union[Dict, None]) -> bool:
        """

        :param response_data: 响应数据
        :param sql_data: 数据库数据
        :return:
        """
        if (response_data and sql_data) is not False:
            if not isinstance(sql_data, dict):
                raise ValueError(
                    "断言失败，response_data、sql_data的数据类型必须要是字典类型，"
                    "请检查接口对应的数据是否正确\n"
                    f"sql_data: {sql_data}, 数据类型: {type(sql_data)}\n"
                )
        return True

    @staticmethod
    def res_sql_data_bytes(res_sql_data: Any) -> Text:
        """ 处理 mysql查询出来的数据类型如果是bytes类型，转换成str类型 """
        if isinstance(res_sql_data, bytes):
            res_sql_data = res_sql_data.decode('utf=8')
        return res_sql_data

    def sql_switch_handle(
            self,
            sql_data: Dict,
            assert_value: Any,
            key: Text,
            values: Any,
            resp_data: Dict,
            message: Text) -> None:
        """

        :param sql_data: 测试用例中的sql
        :param assert_value: 断言内容
        :param key:
        :param values:
        :param resp_data: 预期结果
        :param message: 预期结果
        :return:
        """
        # 判断数据库为开关为关闭状态
        if config.mysql_db.switch is False:
            WARNING.logger.warning(
                "检测到数据库状态为关闭状态，程序已为您跳过此断言，断言值:%s", values
            )
        # 数据库开关为开启
        if config.mysql_db.switch:
            # 走正常SQL断言逻辑
            if sql_data != {'sql': None}:
                res_sql_data = jsonpath(sql_data, assert_value)
                if res_sql_data is False:
                    raise JsonpathExtractionFailed(
                        f"数据库断言内容jsonpath提取失败， 当前jsonpath内容: {assert_value}\n"
                        f"数据库返回内容: {sql_data}"
                    )

                # 判断mysql查询出来的数据类型如果是bytes类型，转换成str类型
                res_sql_data = self.res_sql_data_bytes(res_sql_data[0])
                name = AssertMethod(self.assert_data[key]['type']).name
                self.functions_mapping[name](resp_data[0], res_sql_data, str(message))

            # 判断当用例走的数据数据库断言，但是用例中未填写SQL
            else:
                raise SqlNotFound("请在用例中添加您要查询的SQL语句。")

    def assert_type_handle(
            self,
            assert_types: Union[Text, None],
            sql_data: Union[Dict, None],
            assert_value: Any,
            key: Text,
            values: Dict,
            resp_data: Any,
            message: Text,
            res: Dict
    ) -> None:
        """处理断言类型"""
        # 判断断言类型
        if assert_types == 'SQL':
            self.sql_switch_handle(
                sql_data=sql_data,
                assert_value=assert_value,
                key=key,
                values=values,
                resp_data=resp_data,
                message=message
            )

        # 判断assertType为空的情况下，则走响应断言
        elif assert_types is None:
            name = AssertMethod(self.assert_data[key]['type']).name
            if isinstance(resp_data, str):
                INFO.logger.info("\n断言类型：[%a],预期：[%s],实际：[%s]", name, assert_value, resp_data)
                try:
                    self.functions_mapping[name](resp_data, assert_value, message)
                except Exception as e:
                    text = (
                        # f"<blockquote>\n<b>⭕接口响应校验不一致   {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</b>\n\n"
                        f"<b>⭕接口响应校验不一致   {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</b>\n\n"
                        f"【用例描述】:\n{' ' * 8}{getattr(res, 'detail', '')}\n"
                        f"【请求路径】:\n{' ' * 8}{getattr(res, 'url', '')}\n"
                        f"【请求方式】:\n{' ' * 8}{getattr(res, 'method', '')}\n"
                        f"【请求内容】:\n{' ' * 8}{str(getattr(res, 'request_body', ''))}\n"
                        f"【请求耗时】:\n{' ' * 8}{str(getattr(res, 'res_time', ''))} ms\n"
                        f"【响应状态码】:\n{' ' * 8}{getattr(res, 'status_code', '')}\n"
                        f"【断言类型】:\n{' '* 8}[{name}],预期：[{assert_value}],实际：[{resp_data}]\n"
                        f"【响应内容】:\n{' '* 8}{str(getattr(res, 'response_data', ''))}\n\n"
                        f"<a href='{config.tg.jenkins_skip_url}'>[ 点击我，直接跳转到Jenkins job页面 ]</a>\n"
                        # f"</blockquote>"
                    )
                    tg.sendMessage(text, config.tg.chat_id)
                    raise e
            else:
                INFO.logger.info("\n断言类型：[%a],预期：[%s],实际：[%s]", name, assert_value, resp_data[0])
                try:
                    self.functions_mapping[name](resp_data[0], assert_value, message)
                except Exception as e:
                    # text = (f"<blockquote>\n<b>⭕接口响应校验不一致   {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</b>\n\n"
                    text = (f"<b>⭕接口响应校验不一致   {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</b>\n\n"
                            f"【用例描述】:\n{' ' * 8}{getattr(res, 'detail', '')}\n"
                            f"【请求路径】:\n{' ' * 8}{getattr(res, 'url', '')}\n"
                            f"【请求方式】:\n{' ' * 8}{getattr(res, 'method', '')}\n"
                            f"【请求内容】:\n{' ' * 8}{str(getattr(res, 'request_body', ''))}\n"
                            f"【请求耗时】:\n{' ' * 8}{str(getattr(res, 'res_time', ''))} ms\n"
                            f"【响应状态码】:\n{' ' * 8}{getattr(res, 'status_code', '')}\n"
                            f"【断言类型】:\n{' '* 8}[{name}],预期：[{assert_value}],实际：[{resp_data[0]}]\n"
                            f"【响应内容】:\n{' '* 8}{str(getattr(res, 'response_data', ''))}\n\n"
                            f"<a href='{config.tg.jenkins_skip_url}'>[ 点击我，直接跳转到Jenkins job页面 ]</a>\n"
                            # f"</blockquote>"
                            )
                    tg.sendMessage(text, config.tg.chat_id)
                    raise e
        else:
            text = (
                # f"<blockquote>\n<b>⭕接口响应校验不一致   {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</b>\n\n"
                f"<b>⭕接口响应校验不一致   {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</b>\n\n"
                f"【用例描述】:\n{' ' * 8}{getattr(res, 'detail', '')}\n"
                f"【请求路径】:\n{' ' * 8}{getattr(res, 'url', '')}\n"
                f"【请求方式】:\n{' ' * 8}{getattr(res, 'method', '')}\n"
                f"【请求内容】:\n{' ' * 8}{str(getattr(res, 'request_body', ''))}\n"
                f"【请求耗时】:\n{' ' * 8}{str(getattr(res, 'res_time', ''))} ms\n"
                f"【响应状态码】:\n{' ' * 8}{getattr(res, 'status_code', '')}\n"
                f"【断言类型】:\n{' '* 8}断言失败，目前只支持数据库断言和响应断言\n"
                f"【响应内容】:\n{' '* 8}{str(getattr(res, 'response_data', ''))}\n\n"
                f"<a href='{config.tg.jenkins_skip_url}'>[ 点击我，直接跳转到Jenkins job页面 ]</a>\n"
                # f"</blockquote>"
                )
            tg.sendMessage(text, config.tg.chat_id)
            raise AssertTypeError("断言失败，目前只支持数据库断言和响应断言")

    @classmethod
    def _message(cls, value):
        _message = ""
        if jsonpath(obj=value, expr="$.message") is not False:
            _message = value['message']
        return _message

    def assert_equality(
            self,
            res: Dict) -> None:
        """  assert 断言处理 """
        # 判断数据类型
        # signF = True
        if self._check_params(res.response_data, res.sql_data) is not False:
            for key, values in self.assert_data.items():
                # if key == "status_code":
                #     assert status_code == values
                if key != "status_code":
                    # else:
                    assert_value = self.assert_data[key]['value']  # 获取 yaml 文件中的期望value值
                    if 'jsonpath' in self.assert_data[key]:
                        assert_jsonpath = self.assert_data[key]['jsonpath']  # 获取到 yaml断言中的jsonpath的数据
                        # 从yaml获取jsonpath，拿到对象的接口响应数据
                        resp_data = jsonpath(json.loads(res.response_data), assert_jsonpath)
                    else:
                        resp_data = res.response_data
                    assert_types = self.assert_data[key]['AssertType']
                    message = self._message(value=values)
                    # jsonpath 如果数据获取失败，会返回False，判断获取成功才会执行如下代码
                    if resp_data is not False:
                        # 判断断言类型
                        self.assert_type_handle(
                            assert_types=assert_types,
                            sql_data=res.sql_data,
                            assert_value=assert_value,
                            key=key,
                            values=values,
                            resp_data=resp_data,
                            message=message,
                            res=res
                        )
                    else:
                        ERROR.logger.error("JsonPath值获取失败 %s ", assert_jsonpath)
                        text = (
                            f"<blockquote>\n<b>⭕接口响应校验不一致   {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}</b>\n\n"
                            f"【用例描述】:\n{' ' * 8}{getattr(res, 'detail', '')}\n"
                            f"【请求路径】:\n{' ' * 8}{getattr(res, 'url', '')}\n"
                            f"【请求方式】:\n{' ' * 8}{getattr(res, 'method', '')}\n"
                            f"【请求内容】:\n{' ' * 8}{str(getattr(res, 'request_body', ''))}\n"
                            f"【请求耗时】:\n{' ' * 8}{str(getattr(res, 'res_time', ''))} ms\n"
                            f"【响应状态码】:\n{' ' * 8}{getattr(res, 'status_code', '')}\n"
                            f"【断言类型】:\n{' '* 8}JsonPath值获取失败 {assert_jsonpath}\n"
                            f"【响应内容】:\n{' '* 8}{str(getattr(res, 'response_data', ''))}\n"
                            f"</blockquote>\n"
                            f"<a href='{config.tg.jenkins_skip_url}'>[ 点击我，直接跳转到Jenkins job页面 ]</a>\n"
                            )
                        tg.sendMessage(text, config.tg.chat_id)
                        raise JsonpathExtractionFailed(f"JsonPath值获取失败 {assert_jsonpath}")
                else:
                    try:
                        assert res.status_code == values
                    except Exception as e:
                        raise e
                    # signF = False
        # if signF:
        #     assert status_code == 200


if __name__ == '__main__':
    pass
