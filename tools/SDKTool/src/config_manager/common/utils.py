# -*- coding: utf-8 -*-
"""
Tencent is pleased to support the open source community by making GameAISDK available.

This source code file is licensed under the GNU General Public License Version 3.
For full details, please refer to the file "LICENSE.txt" which is provided as part of this source code package.

Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
"""

import os
import tarfile
import json

DEFAULT_IMAGE_POSTFIX_LIST = [".png", "bmp", ".jpg", ".jpeg"]


def is_dir_has_file(dir_path, postfix_format=None):
    if postfix_format is None:
        postfix_format = DEFAULT_IMAGE_POSTFIX_LIST
    for dir_path, dir_names, file_names in os.walk(dir_path):
        for file in file_names:
            if os.path.splitext(file)[1] in postfix_format:
                return True
    return False


def get_files_count(dir_path, postfix_format=None):
    if postfix_format is None:
        postfix_format = DEFAULT_IMAGE_POSTFIX_LIST

    file_count = 0
    for dir_path, dir_names, file_names in os.walk(dir_path):
        for file in file_names:
            if os.path.splitext(file)[1] in postfix_format:
                file_count = file_count + 1
    return file_count


def make_targz(output_file, source_file):
    if None in [output_file, source_file]:
        raise Exception("failed: input file or output file is None")
    if not os.path.exists(source_file):
        raise ("failed: source file {} is not exists".format(source_file))

    with tarfile.open(output_file, "w:gz") as tar:
        tar.add(source_file, arcname=os.path.basename(source_file))
        return True


def save_file(file_path, content):
    _dir = os.path.dirname(file_path)
    if not os.path.exists(_dir):
        os.mkdir(_dir)
    with open(file_path, "w", encoding="utf8") as f:
        f.write(content)


def load_file(file_path):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r", encoding="utf8") as f:
        content = f.readline()
    return content


def delete_file(file_path):
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as err:
            return False
        else:
            return True
    return True


def load_json_file(file_name):
    try:
        with open(file_name, 'r') as f:
            content = json.load(f)
            return content
    except FileNotFoundError:
        print('file(%s) is not found' % file_name)
    except json.decoder.JSONDecodeError:
        print('json decoder error')
    return {}


def save_json_file(json_file, content, indent=None):
    try:
        with open(json_file, 'w', encoding='utf8') as f:
            json.dump(content, f, indent=indent)
            return True
    except FileNotFoundError:
        print('file(%s) is not found' % json_file)
    return False
