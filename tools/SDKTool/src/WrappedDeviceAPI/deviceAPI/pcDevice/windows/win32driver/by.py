# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import re


class UIElementDescription(object):
    PROPERTY_SEP = '&&'
    OPERATORS = ["=", "~="]
    MATCH_FUNCS = dict()
    MATCH_FUNCS["="] = lambda x, y: x == y
    MATCH_FUNCS["~="] = lambda string, pattern: re.search(pattern, string) is not None

    def __init__(self, value):
        self._parsedValue = self._parse(value)

    def __str__(self):
        """返回格式化后的字符串
        """
        sep = " " + self.PROPERTY_SEP + " "
        tmp = []
        for key in self._parsedValue:
            kv = "%s %s %s" % (key,
                               self._parsedValue[key][0],
                               isinstance(self._parsedValue[key][1], str) and\
                                          '"%s"' % self._parsedValue[key][1] or\
                                          self._parsedValue[key][1])
            tmp.append(kv)
        return sep.join(tmp)

    def _parse(self, value):
        if not value.strip():
            return {}
        props = value.split(self.PROPERTY_SEP)

        parsed_locators = {}
        for prop_str in props:
            prop_str = prop_str.strip()
            if len(prop_str) == 0:
                raise Exception("%s 中含有空的属性。" % value)
            parsed_props = self._parse_property(prop_str)
            parsed_locators.update(parsed_props)
        return parsed_locators

    def _parse_property(self, prop_str):
        """解析property字符串，返回解析后结构

        :sample: 例如将 "ClassName='Dialog' " 解析返回 {ClassName: ['=', 'Dialog']}
        """
        parsed_pattern = "([\w\-]+)\s*([=~!<>]+)\s*[\"'](.*)[\"']"
        match_object = re.match(parsed_pattern, prop_str)
        if match_object is None:
            parsed_pattern = "([\w\-]+)\s*([=~!<>]+)\s*((?:-?0x[0-9a-fA-F]+|-?[0-9]+))"
            match_object = re.match(parsed_pattern, prop_str)
            if match_object is None:
                raise Exception("属性(%s)不符合QPath语法" % prop_str)

            prop_name, operator, prop_value = match_object.groups()
            if not operator in self.OPERATORS:
                raise Exception("QPath不支持操作符：%s"  % operator)
            if prop_value.find('0x') != -1:
                prop_value = int(prop_value, 16)
            else:
                prop_value = int(prop_value)
            return {prop_name: [operator, prop_value]}
        else:
            prop_name, operator, prop_value = match_object.groups()
            if operator not in self.OPERATORS:
                raise Exception("QPath不支持操作符：%s"  % operator)
            return {prop_name: [operator, prop_value]}

    def loads(self):
        """获取解释后的数值
        """
        return self._parsedValue


class QPath(object):
    """Query Path类，使用QPath字符串定位UI控件

    QPath的定义：
    Qpath ::= Seperator UIElementDescription Qpath
    Seperator ::= 路径分隔符，任意的单个字符
    UIElementDescription ::= UIElementProperty [&& UIElementProperty]
    UIElementProperty ::= UIProperty | RelationProperty | IndexProperty
    UIProperty ::= Property Operator “Value”
    RelationProperty ::= MaxDepth = Integer(最大搜索子孙深度， 若不写，则代表搜索所有子孙。 数值从1开始)
    IndexProperty ::= Index = Integer(Integer:找到的多个控件中的第几个（数值从0开始）)

    Operator ::= '=' | '~=' ('=' 表示精确匹配; '~=' 表示用正则表达式匹配)

    UI控件基本上都是由树形结构组织起来的。为了方便定位树形结构的节点，QPath采用了路径结构
         的字符串形式。 QPath以第一个字符为路径分隔符，如 "/Node1/Node2/Node3"和 “|Node1|Node2|Node3"
         是一样的路径，都表示先找到Node1，再在Node1的子孙节点里找Node2，然后在Node2的子孙节点里
         找Node3。而定位每个Node需要改节点的多个属性以"&&"符号连接起来, 形成
    "/Property1='value1' && property2~='value2' && ..."的形式，其中"~="表示正则匹配。
    "MaxDepth"表示该节点离祖先节点的最大深度，    如果没有明确指定时默认取值为'1',即直接父子关系。
    QPath还支持"Index”属性，用于当找到多个节点时指定选择第几个节点。

         例子：
    Qpath ="/ ClassName='TxGuiFoundation' && Caption~='QQ\d+' && Index='0'
            / Name='mainpanel' && MaxDepth='10'"
    """
    PROPERTY_SEP = '&&'

    def __init__(self, value):
        """Contructor

        :type value: string
        :param value: QPath字符串
        """
        if not isinstance(value, str):
            raise Exception("输入的QPath(%s)不是字符串!" % value)
        self._strqpath = value
        self._path_sep, self._parsed_qpath = self._parse(value)
        self._error_qpath = None

    def _parse(self, qpath_string):
        """解析qpath，并返回QPath的路径分隔符和解析后的结构

           "| ClassName='Dialog' && Caption~='SaveAs' | UIType='GF' && ControlID='123' && Instanc='-1'"
           => [{'ClassName': ['=', 'Dialog'], 'Caption': ['~=', 'SaveAs']},
               {'UIType': ['=', 'GF'], 'ControlID': ['=', '123'], 'Index': ['=', '-1']}]

        :param qpath_string: qpath 字符串
        :return: (seperator, parsed_qpath)
        """
        qpath_string = qpath_string.strip()
        seperator = qpath_string[0]
        locators = qpath_string[1:].split(seperator)
        parsed_qpath = []
        for locator in locators:
            parsed_locators = UIElementDescription(locator).loads()
            parsed_qpath.append(parsed_locators)

        return seperator, parsed_qpath

    def __str__(self):
        """返回格式化后的QPath字符串
        """
        qpath_str = ""
        for locator in self._parsed_qpath:
            qpath_str += self._path_sep + " "
            delimit_str = " "  + self.PROPERTY_SEP + " "
            locator_str = delimit_str.join(["%s %s '%s'"  % (key, locator[key][0], locator[key][1]) for key in locator])
            qpath_str += locator_str

        return qpath_str

    def loads(self, level=-1):
        """获取解释后的数值

        :level: int, the index of prop list
        :raise: ValueError, when level is invalid
        :return: dict
        """
        if level == -1:
            return self._parsed_qpath
        else:
            if 0 <= level < len(self._parsed_qpath):
                return self._parsed_qpath[level]
            raise ValueError('error parameter level:%s' % level)

    def get_parsed_qpath(self):
        """获取解析后的数据

        :return:
        """
        return self._parsed_qpath
