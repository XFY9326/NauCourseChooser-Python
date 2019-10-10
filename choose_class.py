# coding=utf-8
from datetime import datetime

import class_submit
import config
import io_manage
import jwc_info

get_class_type_list = False
get_class_list = {}


def choose(jwc_session, user_url, choose_class_info_list):
    global get_class_type_list
    if not get_class_type_list:
        class_type_list = jwc_info.get_available_class_type(jwc_session, user_url)
        if class_type_list:
            get_class_type_list = True
            io_manage.save_data(config.data_key_class_type_list, class_type_list)
    else:
        class_type_list = io_manage.read_data(config.data_key_class_type_list, False)

    if class_type_list:
        while True:
            i = 0
            item_array = []
            key_array = []
            print('\n请按序号选择需要抢的课程类别：')
            for key in class_type_list.keys():
                i = i + 1
                print('%d ->%s' % (i, key))
                item_array.append(class_type_list[key])
                key_array.append(key)
            print('0 ->准备抢课')
            print('-1->查看所有已经选择的课程')
            print('-2->注销登陆并退出抢课脚本')

            class_type_int = io_manage.input_select_array(-2, len(class_type_list))

            if class_type_int == -1:
                if len(choose_class_info_list) == 0:
                    print('\n你还没有选择需要抢的课程！')
                else:
                    print('\n已选课程列表：')
                    show_all_class(choose_class_info_list)
            elif class_type_int == -2:
                break
            elif class_type_int == 0:
                if len(choose_class_info_list) == 0:
                    print('\n你还没有选择需要抢的课程！')
                elif set_class_submit_info(jwc_session, choose_class_info_list):
                    break
            else:
                if not (item_array[class_type_int - 1] in choose_class_info_list.keys()):
                    info_list = {}
                else:
                    info_list = choose_class_info_list[item_array[class_type_int - 1]]

                info_list = choose_detail(jwc_session, info_list, item_array[class_type_int - 1],
                                          key_array[class_type_int - 1])
                if info_list:
                    choose_class_info_list[item_array[class_type_int - 1]] = info_list
    else:
        print('课程类型列表获取错误')


def choose_detail(jwc_session, choose_class_info_list, class_type_url, class_type_name):
    global get_class_list
    in_time = True

    if not (class_type_url in get_class_list.items()) or not get_class_list[class_type_url]:
        class_list = jwc_info.get_available_class(jwc_session, config.jwc_student_url + class_type_url)
        if class_list:
            get_class_list[class_type_url] = True
            io_manage.save_data(config.data_key_class_list, class_list)
    else:
        class_list = io_manage.read_data(config.data_key_class_list, False)

    if class_list:

        if len(class_list['class_list']) == 0:
            print('\n此类型课程并没有可选的课！')
            return False

        choose_class_info_list['data'] = {
            'term': class_list['term'],
            'startDate': class_list['s'],
            'endDate': class_list['e'],
            'limitNum': class_list['limit'],
            'CourseSelectStyle': class_list['select_style'],
            'banRule': class_list['rule']}
        choose_class_info_list['submitType'] = class_list['submit']
        choose_class_info_list['typeName'] = class_type_name
        if not ('class' in choose_class_info_list):
            choose_class_info_list['class'] = []

        end_time = datetime.strptime(class_list['end_date'], "%Y/%m/%d %H:%M:%S")
        now_time = datetime.now()
        if now_time > end_time:
            in_time = False
            print('\n此类型课程已经结束选课！')
            if not io_manage.input_yes_or_no('\n你是否要继续查看待选的课程？', False):
                return False

        i = 0
        if in_time:
            print('\n请按序号选择需要抢的课程：')
        else:
            print('\n当前类型显示的课程只能查看：')
        for info in class_list['class_list']:
            i = i + 1
            output = ''
            for detail in info.keys():
                if not ('序号' in detail or info[detail] == '' or info[detail] == '--'):
                    output = output + detail + ': ' + info[detail] + ', '
            if len(output) >= 2:
                output = output[:-2]
            print('%d ->%s' % (i, output))

        print('0 ->返回课程类型列表')
        if in_time:
            print('-1->查看当前课程类型下已经选择的课程')
            print('-2->清空当前课程类型下已经选择的课程')
            print('-3->清空已选课程并选中所有课程为备选课程')

        while True:
            class_int = io_manage.input_select_array(-3, len(class_list['class_list']))
            if class_int == 0:
                break
            elif class_int == -1 and in_time:
                if not ('class' in choose_class_info_list.keys()):
                    choose_class_info = []
                else:
                    choose_class_info = choose_class_info_list['class']
                if len(choose_class_info) == 0:
                    print('\n你在该课程类型下没有选择任何课程！')
                else:
                    print('\n你已经选择的课程为：')
                    for info in choose_class_info:
                        is_sub = ''
                        if info['sub_class']:
                            is_sub = '(备选课程)'
                        output = '%s(%s):%s_%s' % (info['课程名称'], info['课程ID'], info['教师'], info['教学班'])
                        print(output + is_sub)
            elif class_int == -2 and in_time:
                if io_manage.input_yes_or_no('\n你是否要清空该课程类别下所有已选课程？', False):
                    choose_class_info_list['class'] = []
                    print('清空该课程类别下所有已选课程成功！\n')
            elif in_time:
                if not ('class' in choose_class_info_list.keys()):
                    choose_class_info = []
                else:
                    choose_class_info = choose_class_info_list['class']
                if int(class_list['limit']) != 0 and len(choose_class_info) >= int(class_list['limit']):
                    print('\n你选择的课程已经满了！')
                    if io_manage.input_yes_or_no('你是否要将此课程加入备选课程？(备选课程会在尝试完其他课程后开始抢)', False):
                        found = False
                        for info in choose_class_info:
                            if info['课程ID'] == class_list['class_list'][class_int - 1]['课程ID'] and info['教学班'] == \
                                    class_list['class_list'][class_int - 1]['教学班']:
                                found = True
                                break
                        if found:
                            print('\n你已经选过这门课程了！')
                        else:
                            class_list['class_list'][class_int - 1]['sub_class'] = True
                            choose_class_info.append(class_list['class_list'][class_int - 1])
                            choose_class_info_list['class'] = choose_class_info
                            print('\n课程添加成功！')
                elif class_int == -3:
                    if io_manage.input_yes_or_no('\n你是否要清空已选课程并选中所有课程为备选课程？(扫课专用)', False):
                        choose_class_info_list['class'] = []
                        for classes in class_list['class_list']:
                            classes['sub_class'] = True
                            choose_class_info.append(classes)
                        choose_class_info_list['class'] = choose_class_info
                        print('\n所有课程添加成功！')
                else:
                    found = False
                    for info in choose_class_info:
                        if info['课程ID'] == class_list['class_list'][class_int - 1]['课程ID'] and info['教学班'] == \
                                class_list['class_list'][class_int - 1]['教学班']:
                            found = True
                            break
                    if found:
                        print('\n你已经选过这门课程了！')
                    else:
                        class_list['class_list'][class_int - 1]['sub_class'] = False
                        choose_class_info.append(class_list['class_list'][class_int - 1])
                        choose_class_info_list['class'] = choose_class_info
                        print('\n课程添加成功！')
            else:
                print('\n当前类型显示的课程只能查看不能选择！')
        return choose_class_info_list
    else:
        print('课程列表获取错误')
        return False


def set_class_submit_info(jwc_session, choose_class_info_list, scan_class=False):
    if io_manage.input_yes_or_no('\n请问是否需要保存本次课程选择记录？', False):
        io_manage.save_data(config.data_key_class_choose_list, choose_class_info_list)

    input_num = input('\n请输入共尝试几轮(默认5轮):')
    if not input_num.isdigit() or int(input_num) <= 0:
        total_num = 5
    else:
        total_num = int(input_num)

    input_num = input('\n请输入每节课的每一轮的尝试次数(默认1次，较大次数可能会导致重复抢课问题):')
    if not input_num.isdigit() or int(input_num) <= 0:
        try_num = 1
    else:
        try_num = int(input_num)

    input_num = input('\n请输入每次抢课抢课超时时间秒数(默认20秒，超时就会放弃改次抢课):')
    if not input_num.isdigit() or int(input_num) <= 0:
        time_out_num = 20
    else:
        time_out_num = int(input_num)

    if not scan_class:
        scan_class = io_manage.input_yes_or_no('\n请问是否开启扫课模式？(人数已满不会自动移除)', False)

    input('\n<按下回车键开始抢课>')

    all_class_get = False
    while True:
        for i in range(0, total_num):
            try:
                result = class_submit.data_submit(jwc_session, choose_class_info_list, try_num, time_out_num,
                                                  scan_class)
                print('%s%d%s' % ('本次第', i + 1, '轮抢课结果：'))
                for key in result.keys():
                    print(key + ': ' + result[key])
                    if '自动移除' in result[key]:
                        result_info = key.split('_')
                        class_id = key[key.index("(") + 1:key.index(")")]
                        choose_class_info_list = del_class(choose_class_info_list, class_id, result_info[1])
                all_class_get = not check_class(choose_class_info_list)
                if all_class_get:
                    print('抢课结束，所有课程已经抢到！\n')
                    break
            except KeyboardInterrupt:
                break

        if not all_class_get:
            if not io_manage.input_yes_or_no('\n是否继续尝试抢课？', True):
                break
        else:
            break

    return False


def del_class(class_list, class_id, class_name):
    for class_type in class_list.keys():
        for _ in class_list[class_type]:
            for classes in class_list[class_type]['class']:
                if classes['课程ID'] == class_id and classes['教学班'] == class_name:
                    class_list[class_type]['class'].remove(classes)
                    break

    return class_list


def check_class(class_list):
    for class_type in class_list.keys():
        if len(class_list[class_type]['class']) != 0:
            return True
    return False


def show_all_class(class_list):
    for class_type in class_list.keys():
        for classes in class_list[class_type]['class']:
            is_sub = ''
            if classes['sub_class']:
                is_sub = '(备选课程)'
            output = '%s->%s(%s):%s_%s' % (
                class_list[class_type]['typeName'], classes['课程名称'], classes['课程ID'], classes['教师'], classes['教学班'])
            print(output + is_sub)
