# coding=utf-8
import json
import os

import config


def input_select_array(input_min, input_max):
    while True:
        input_str = input('请选择：')
        if input_str == '':
            continue
        try:
            input_int = int(input_str)
            if input_min <= input_int <= input_max:
                return input_int
            else:
                print('输入错误，请重试！')
        except:
            print('输入错误，请重试！')
            pass


def input_yes_or_no(question, default):
    if default:
        output_str = 'Y/n'
    else:
        output_str = 'y/N'
    input_str = input(question + '(' + output_str + '):')
    if input_str.lower() == 'y':
        return True
    elif input_str.lower() == 'n':
        return False
    else:
        return default


def save_json_data(json_data):
    with open(config.data_file_name, 'w') as file_obj:
        json.dump(json_data, file_obj, indent=4)


def read_json_data():
    if os.path.exists(config.data_file_name) and os.path.isfile(config.data_file_name):
        with open(config.data_file_name) as file_obj:
            return json.load(file_obj)
    else:
        return False


def save_data(key, data):
    input_data = {}
    read_result = read_json_data()
    if read_result:
        input_data = read_result
    input_data[key] = data
    save_json_data(input_data)


def read_data(key, default):
    read_result = read_json_data()
    if read_result and key in read_result:
        return read_result[key]
    else:
        return default


def del_data(key):
    read_result = read_json_data()
    if read_result and key in read_result:
        del read_result[key]
        save_json_data(read_result)
        return True
    else:
        return False
