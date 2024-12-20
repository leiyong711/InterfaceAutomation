#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @project name: mc_aggregator_pyauto
# @Time   : 2024/12/20 10:35
# @Author  : leo

import os
import traceback
import pytest
from io import StringIO

from utils.other_tools.models import NotificationType
from utils.other_tools.allure_data.allure_report_data import AllureFileClean
from utils.logging_tool.log_control import INFO
from utils.notify.wechat_send import WeChatSend
from utils.notify.ding_talk import DingTalkSendMsg
from utils.notify.send_mail import SendEmail
from utils.notify.lark import FeiShuTalkChatBot
from utils.other_tools.allure_data.error_case_excel import ErrorCaseExcel
from utils import config
from utils.read_files_tools.case_automatic_control import TestCaseAutomaticGeneration


def run():
    # 从配置文件中获取项目名称
    try:
        INFO.logger.info(
            """
                             _    _         _      _____         _
              __ _ _ __ (_)  / \\  _   _| |_ __|_   _|__  ___| |_
             / _` | '_ \\| | / _ \\| | | | __/ _ \\| |/ _ \\/ __| __|
            | (_| | |_) | |/ ___ \\ |_| | || (_) | |  __/\\__ \\ |_
             \\__,_| .__/|_/_/   \\_\\__,_|\\__\\___/|_|\\___||___/\\__|
                  |_|
                  开始执行{}项目...
                """.format(config.project_name)
        )

        # 判断现有的测试用例，如果未生成测试代码，则自动生成
        # TestCaseAutomaticGeneration().get_case_automatic()

        pytest.main(['-s', '-W', 'ignore:Module already imported:pytest.PytestWarning',
                     '--alluredir', './report/tmp', "--clean-alluredir"])

        """
                   --reruns: 失败重跑次数
                   --count: 重复执行次数
                   -v: 显示错误位置以及错误的详细信息
                   -s: 等价于 pytest --capture=no 可以捕获print函数的输出
                   -q: 简化输出信息
                   -m: 运行指定标签的测试用例
                   -x: 一旦错误，则停止运行
                   --maxfail: 设置最大失败次数，当超出这个阈值时，则不会在执行测试用例
                    "--reruns=3", "--reruns-delay=2"
                   """

        os.system(r"allure generate ./report/tmp -o ./report/html --clean")
        # 接口巡检时不需要生成测试报告
        if config.execution_type == 1:
            return
        allure_data = AllureFileClean().get_case_count()
        notification_mapping = {
            NotificationType.DING_TALK.value: DingTalkSendMsg(allure_data).send_ding_notification,
            NotificationType.WECHAT.value: WeChatSend(allure_data).send_wechat_notification,
            NotificationType.EMAIL.value: SendEmail(allure_data).send_main,
            NotificationType.FEI_SHU.value: FeiShuTalkChatBot(allure_data).post
        }

        if config.notification_type != NotificationType.DEFAULT.value:
            notification_mapping.get(config.notification_type)()

        if config.excel_report:
            ErrorCaseExcel().write_case()

        # 程序运行之后，自动启动报告，如果不想启动报告，可注释这段代码
        # os.system(f"allure serve ./report/tmp -h 127.0.0.1 -p 9999")


    except Exception:
        # 如有异常，相关异常发送邮件
        e = traceback.format_exc()
        send_email = SendEmail(AllureFileClean.get_case_count())
        send_email.error_mail(e)
        raise


if __name__ == '__main__':
    # cov = coverage.coverage()
    # cov.start()
    run()
    # cov.stop()
    # cov.save()
    # # 命令行模式展示结果
    # # cov.report()
    # output = StringIO()
    # cov.report(file=output)
    # # 将 StringIO 对象的内容转换为字符串
    # output_str = output.getvalue()
    # lines = output_str.split('\n')
    # formatted_output = ''
    # column_widths = [78, 6, 6, 6]
    # for line in lines:
    #     parts = line.split()
    #     formatted_line = ''
    #     for i in range(len(parts)):
    #         formatted_part = parts[i].ljust(column_widths[i])
    #         formatted_line += formatted_part + '\t'
    #     formatted_output += formatted_line + '\n'  # 添加空格以便于分隔不同列
    # outputStr = "\n本地测试代码覆盖率:\n" + formatted_output
    # allure_data = AllureFileClean().get_case_count()
    # notification_mapping = {
    #     NotificationType.DING_TALK.value: DingTalkSendMsg(allure_data).send_ding_notification,
    #     NotificationType.WECHAT.value: WeChatSend(allure_data).send_wechat_notification,
    #     NotificationType.EMAIL.value: SendEmail(allure_data).send_main(outputStr),
    #     NotificationType.FEI_SHU.value: FeiShuTalkChatBot(allure_data).post
    # }

    # if config.notification_type != NotificationType.DEFAULT.value:
    #     notification_mapping.get(config.notification_type)()
    #
    # if config.excel_report:
    #     ErrorCaseExcel().write_case()
    # 生成HTML覆盖率报告
    # cov.html_report(directory='covhtml')
