#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @project name: mc_aggregator_pyauto
# @Time   : 2024/12/20 11:11
# @Author  : leo


def jsonpath_replace(change_data, key_name, data_switch=None):
    """处理jsonpath数据"""
    _new_data = key_name + ''
    for i in change_data:
        if i == '$':
            pass
        elif data_switch is None and i == "data":
            _new_data += '.data'
        elif i[0] == '[' and i[-1] == ']':
            _new_data += "[" + i[1:-1] + "]"
        else:
            _new_data += '[' + '"' + i + '"' + "]"
    return _new_data


if __name__ == '__main__':
    jsonpath_replace(change_data=['$', 'data', 'id'], key_name='self.__yaml_case')
