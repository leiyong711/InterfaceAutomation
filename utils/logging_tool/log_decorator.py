#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @project name: mc_aggregator_pyauto
# @Time   : 2024/12/20 10:58
# @Author  : leo

"""
日志装饰器，控制程序日志输入，默认为 True
如设置 False，则程序不会打印日志
"""
import ast
from functools import wraps
from utils.read_files_tools.regular_control import cache_regular
from utils.logging_tool.log_control import INFO, ERROR
from utils import config


def log_decorator(switch: bool):
    """
    封装日志装饰器, 打印请求信息
    :param switch: 定义日志开关
    :return:
    """
    def decorator(func):
        @wraps(func)
        def swapper(*args, **kwargs):

            # 判断日志为开启状态，才打印日志
            res = func(*args, **kwargs)
            # 判断日志开关为开启状态
            if switch:
                _log_msg = f"\n======================================================\n" \
                               f"用例标题: {getattr(res, 'detail', '')}\n" \
                               f"请求路径: {getattr(res, 'url', '')}\n" \
                               f"请求方式: {getattr(res, 'method', '')}\n" \
                               f"请求头:   {getattr(res, 'headers', '')}\n" \
                               f"请求内容: {getattr(res, 'request_body', '')}\n" \
                               f"接口响应内容: {getattr(res, 'response_data', '')}\n" \
                               f"接口响应时长: {getattr(res, 'res_time', '')} ms\n" \
                               f"Http状态码: {getattr(res, 'status_code', '')}\n" \
                               "====================================================="
                if config.execution_type == 1:
                    # 线上巡检，yaml文件未注明的用例，默认不执行
                    _is_run = ast.literal_eval(cache_regular(str(getattr(res, 'is_run', 'False'))))
                else:
                    # 冒烟测试，yaml文件未注明的用例，默认都执行
                    _is_run = ast.literal_eval(cache_regular(str(getattr(res, 'is_run', 'True'))))
                # 判断正常打印的日志，控制台输出绿色
                if _is_run in (True, None) and res.status_code == 200:
                    INFO.logger.info(_log_msg)
                else:
                    # 失败的用例，控制台打印红色
                    ERROR.logger.error(_log_msg)
            return res
        return swapper
    return decorator
