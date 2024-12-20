#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @project name: mc_aggregator_pyauto
# @Time   : 2024/12/20 10:52
# @Author  : leo

import pytest
import time
import allure
import requests
import ast
from common.setting import ensure_path_sep
from utils.requests_tool.request_control import cache_regular
from utils.logging_tool.log_control import INFO, ERROR, WARNING
from utils.other_tools.models import TestCase
from utils.read_files_tools.clean_files import del_file
from utils.other_tools.allure_data.allure_tools import allure_step, allure_step_no
from utils.cache_process.cache_control import CacheHandler
from urllib.parse import urlencode
from utils import config
from utils.notify.tg import TgApi

tg = TgApi()


@pytest.fixture(scope="session", autouse=False)
def clear_report():
    """如clean命名无法删除报告，这里手动删除"""
    del_file(ensure_path_sep("\\report"))


@pytest.fixture(scope="session", autouse=True)
def work_login_init():
    from utils import config
    """
    获取登录的cookie
    :return:
    """
    #
    url = config.host + "/auth/oauth2/token"
    data = {"grant_type": "password", "scope": "server", "username": "86:18216060752",
            "password": "Uzf0aekR9TQ=", "phoneCode": "86"}

    data = {"grant_type": "password", "scope": "server", "username": "testdemo_03@163.com",
            "password": "QiT0aekR9TQ=", "email": ""}
    headers = {'authorization': 'Basic Y3VzdG9tOmN1c3RvbQ==', 'client-toc': 'Y',
               'content-type': 'application/x-www-form-urlencoded'}
    # 请求登录接口
    try:
        res = requests.request("POST", url, data=data, headers=headers, verify=False)
        res_json = res.json()
        INFO.logger.info(f"测试登录: {res_json}")
        token = ""
        if 'access_token' in res_json:
            # 提取 "token" 内容
            token = res_json['access_token']
        CacheHandler.update_cache(cache_name='login_token', value=token)
    except ConnectionError:
        INFO.logger.info("work_login_init方法，获取会话token失败，请检查")
    # 管理后台的token
    AdminData = {"grant_type": "password", "scope": "server", "username": "17620320675",
                 "password": "Uzf0aekR9TQ="}
    headers = {'authorization': 'Basic Y3VzdG9tOmN1c3RvbQ==',
               'content-type': 'application/x-www-form-urlencoded'}
    try:
        res = requests.request("POST", f"{config.backend_host}/auth/oauth2/token", data=AdminData, headers=headers, verify=False)
        res_json = res.json()
        token = ""
        if 'access_token' in res_json:
            # 提取 "token" 内容
            token = res_json['access_token']
        CacheHandler.update_cache(cache_name='AdminToken', value=token)
    except ConnectionError:
        INFO.logger.info("work_login_init方法，获取会话adminToken失败，请检查")


def pytest_collection_modifyitems(items):
    """
    测试用例收集完成时，将收集到的 item 的 name 和 node_id 的中文显示在控制台上
    :return:
    """
    for item in items:
        item.name = item.name.encode("utf-8").decode("unicode_escape")
        item._nodeid = item.nodeid.encode("utf-8").decode("unicode_escape")

    # 期望用例顺序
    # print("收集到的测试用例:%s" % items)
    appoint_items = ["test_get_user_info", "test_collect_addtool", "test_Cart_List", "test_ADD", "test_Guest_ADD",
                     "test_Clear_Cart_Item"]

    # 指定运行顺序
    run_items = []
    for i in appoint_items:
        for item in items:
            module_item = item.name.split("[")[0]
            if i == module_item:
                run_items.append(item)

    for i in run_items:
        run_index = run_items.index(i)
        items_index = items.index(i)

        if run_index != items_index:
            n_data = items[run_index]
            run_index = items.index(n_data)
            items[items_index], items[run_index] = items[run_index], items[items_index]
    # 如果需要顺序执行，就修改appoint_classes的内容
    # appoint_classes = { "TestLogin": [],"TestZzzww": []}
    # for item in items:
    #     for cls_name in appoint_classes:
    #         if item.parent.name == cls_name:
    #             appoint_classes[cls_name].append(item)
    #             # print("收集到的测试用例名称:%s" % item)
    # items.clear()
    # for cases in appoint_classes.values():
    #     items.extend(cases)


def pytest_configure(config):
    config.addinivalue_line("markers", 'smoke')
    config.addinivalue_line("markers", '回归测试')


@pytest.fixture(scope="function", autouse=True)
def case_skip(in_data):
    """处理跳过用例"""
    in_data = TestCase(**in_data)
    if ast.literal_eval(cache_regular(str(in_data.is_run))) is False:
        allure.dynamic.title(in_data.detail)
        allure_step_no(f"请求URL: {in_data.is_run}")
        allure_step_no(f"请求方式: {in_data.method}")
        allure_step("请求头: ", in_data.headers)
        allure_step("请求数据: ", in_data.data)
        allure_step("依赖数据: ", in_data.dependence_case_data)
        allure_step("预期数据: ", in_data.assert_data)
        pytest.skip()


def pytest_terminal_summary(terminalreporter):
    """
    收集测试结果
    """

    _PASSED = len([i for i in terminalreporter.stats.get('passed', []) if i.when != 'teardown'])
    _ERROR = len([i for i in terminalreporter.stats.get('error', []) if i.when != 'teardown'])
    _FAILED = len([i for i in terminalreporter.stats.get('failed', []) if i.when != 'teardown'])
    _SKIPPED = len([i for i in terminalreporter.stats.get('skipped', []) if i.when != 'teardown'])
    _TOTAL = terminalreporter._numcollected
    _TIMES = time.time() - terminalreporter._sessionstarttime
    INFO.logger.error(f"用例总数: {_TOTAL}")
    INFO.logger.error(f"异常用例数: {_ERROR}")
    ERROR.logger.error(f"失败用例数: {_FAILED}")
    WARNING.logger.warning(f"跳过用例数: {_SKIPPED}")
    INFO.logger.info("用例执行时长: %.2f" % _TIMES + " s")

    try:
        _RATE = _PASSED / _TOTAL * 100
        INFO.logger.info("用例成功率: %.2f" % _RATE + " %")
    except ZeroDivisionError:
        INFO.logger.info("用例成功率: 0.00 %")

    if config.execution_type == 1 and config.tg_inspection_results == 'info':
        total = _TOTAL - _SKIPPED
        try:
            rate = _PASSED / total * 100
        except:
            rate = 0.00
        placeholders = ' ' * 4
        text = (f'<pre><code class="language-✅定时巡检结束  {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}">\n'
                f"<b>本次执行结果如下:</b>\n"
                f"【用例总数】:\n{placeholders}{total}\n"
                f"【通过用例数】:\n{placeholders}{_PASSED}\n"
                f"【异常用例数】:\n{placeholders}{_ERROR}\n"
                f"【失败用例数】:\n{placeholders}{_FAILED}\n"
                f"【用例执行时长】:\n{placeholders}{str(round(_TIMES,2))} ms\n"
                f"【用例成功率】:\n{placeholders}{str(round(rate,2))} %\n"
                f"</code></pre>\n\n"
                f"<a href='{config.tg.jenkins_skip_url}'>[ 点击我，直接跳转到Jenkins job页面 ]</a>\n"
                )
        tg.sendMessage(text, config.tg.chat_id)
