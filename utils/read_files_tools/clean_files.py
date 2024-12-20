#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @project name: mc_aggregator_pyauto
# @Time   : 2024/12/20 11:13
# @Author  : leo

import os


def del_file(path):
    """删除目录下的文件"""
    list_path = os.listdir(path)
    for i in list_path:
        c_path = os.path.join(path, i)
        if os.path.isdir(c_path):
            del_file(c_path)
        else:
            os.remove(c_path)
