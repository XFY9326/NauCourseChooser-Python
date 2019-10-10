# coding=utf-8
import copy
import random
import requests
import time
from threading import Thread

import config

jwc_header = None


def data_submit(jwc_session, class_list, try_count, time_out, scan_class):
    thread = {}

    for class_type in class_list.keys():
        data = class_list[class_type]['data']
        submit_type = class_list[class_type]['submitType']
        for classes in class_list[class_type]['class']:
            if not classes['sub_class'] or check_only_sub_class(class_list[class_type]['class']):
                count = 0
                while count < try_count:
                    key_name = '%s->%s(%s):%s_%s_%d' % (
                        class_list[class_type]['typeName'], classes['课程名称'],
                        classes['课程ID'], classes['教师'], classes['教学班'], count)

                    if submit_type == 'RepairGroup_Submit':
                        thread[key_name] = class_repair_group_submit(jwc_session, classes['课程ID'], classes['教学班'], data,
                                                                     time_out)
                    elif submit_type == 'EngExpandSubmit':
                        thread[key_name] = class_eng_expand_submit(jwc_session, classes['课程ID'], classes['教学班'], data,
                                                                   time_out)
                    elif submit_type == 'ZX_Submit':
                        thread[key_name] = class_submit(jwc_session, classes['课程ID'], classes['教学班'], data, time_out)
                    else:
                        thread[key_name] = class_submit(jwc_session, classes['课程ID'], classes['教学班'], data, time_out)

                    count = count + 1

    time_start = time.time()
    for i in thread:
        thread[i].start()

    result = {}
    result_str = {}
    for i in thread.keys():
        thread[i].join()
        result[i] = thread[i].get_result()

        if type(result[i]) is requests.models.Response:
            result_str[i] = str(result[i].text)
            result[i].close()
        else:
            result_str[i] = result[i]

        if '系统错误提示页' in result_str[i]:
            result_str[i] = '系统请求错误！'
        elif '系统不在开放时间内' in result_str[i]:
            result_str[i] = '系统不在开放时间内，请稍后再试'
        elif '已经选修' in result_str[i]:
            result_str[i] = '该课程已经选修（脚本将会自动移除此抢课课程）'
        elif '同名课程' in result_str[i]:
            result_str[i] = '已经修过同名课程（脚本将会自动移除此抢课课程）'
        elif '超出当前批次' in result_str[i]:
            result_str[i] = '超出当前批次最大选课限制（脚本将会自动移除此抢课课程）'
        elif '已经选满' in result_str[i]:
            result[i] = '该课程已经选满 (脚本将会自动移除此抢课课程）'
        elif '人数已满' in result_str[i]:
            result_str[i] = '该课程人数已满'
            if not scan_class:
                result_str[i] += ' (脚本将会自动移除此抢课课程）'
        elif '超过最大学分' in result_str[i]:
            result_str[i] = '当前选课已经超过最大学分需求 (脚本将会自动移除此抢课课程）'
        elif '安排相冲突' in result_str[i]:
            result_str[i] = '当前选课与课表课程存在冲突 (脚本将会自动移除此抢课课程）'
        elif '时间相冲突' in result_str[i]:
            result_str[i] = '当前选课与其他选课存在冲突 (脚本将会自动移除此抢课课程）'
        elif '不得选修' in result_str[i]:
            result_str[i] = '当前选课不得选修 (脚本将会自动移除此抢课课程）'
        elif '添加成功' in result_str[i]:
            result_str[i] = '选课添加成功（脚本将会自动移除此抢课课程）'
        else:
            result_str[i] += ' （未知反馈，非乱码请上报开发者，谢谢）'

    time_end = time.time()
    print('%s:%.3f%s' % ('\n本次抢课总耗时', time_end - time_start, 's'))
    return result_str


def check_only_sub_class(class_info_list):
    for classes in class_info_list:
        if not classes['sub_class']:
            return False
    return True


def class_submit(jwc_session, course_id, teaching_class, data, time_out):
    url = config.jwc_server + 'Servlet/AddCourseSelectModel.ashx'
    return class_data_submit(jwc_session, url, course_id, teaching_class, data, time_out)


def class_zx_submit(jwc_session, course_id, teaching_class, data, time_out):
    return class_submit(jwc_session, course_id, teaching_class, data, time_out)


def class_repair_group_submit(jwc_session, course_id, teaching_class, data, time_out):
    url = config.jwc_server + 'Servlet/AddRepairGroupCourseSelectModel.ashx'
    return class_data_submit(jwc_session, url, course_id, teaching_class, data, time_out)


def class_eng_expand_submit(jwc_session, course_id, teaching_class, data, time_out):
    url = config.jwc_server + 'Servlet/AddEngCourseSelectModel.ashx'
    return class_data_submit(jwc_session, url, course_id, teaching_class, data, time_out)


def class_data_submit(jwc_session, url, course_id, teaching_class, data, time_out):
    data['courseID'] = course_id
    data['teachingClass'] = teaching_class
    return NetWorkThread(post_class_data, args=(jwc_session, url, copy.deepcopy(data), time_out))


def post_class_data(jwc_session, url, data, time_out):
    try:
        return jwc_session.post(url, data, timeout=time_out, headers=get_header())
    except TimeoutError:
        return "抢课时间超时！"
    except:
        return "请求时出现错误"


class NetWorkThread(Thread):
    def __init__(self, func, args=()):
        super(NetWorkThread, self).__init__()
        self.func = func
        self.args = args
        self.result = None

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        return self.result


def get_header():
    global jwc_header
    if jwc_header is None:
        head_user_agent = ['Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
                           'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 '
                           'Safari/537.36',
                           'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; SLCC2; .NET CLR 2.0.50727; .NET CLR '
                           '3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; rv:11.0) like Gecko)',
                           'Mozilla/5.0 (Windows; U; Windows NT 5.2) Gecko/2008070208 Firefox/3.0.1',
                           'Mozilla/5.0 (Windows; U; Windows NT 5.1) Gecko/20070309 Firefox/2.0.0.3',
                           'Mozilla/5.0 (Windows; U; Windows NT 5.1) Gecko/20070803 Firefox/1.5.0.12',
                           'Opera/9.27 (Windows NT 5.2; U; zh-cn)',
                           'Mozilla/5.0 (Macintosh; PPC Mac OS X; U; en) Opera 8.0',
                           'Opera/8.0 (Macintosh; PPC Mac OS X; U; en)',
                           'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.12) Gecko/20080219 '
                           'Firefox/2.0.0.12 Navigator/9.0.0.6',
                           'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Win64; x64; Trident/4.0)',
                           'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0)',
                           'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; SLCC2; .NET CLR '
                           '2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.2; '
                           '.NET4.0C; .NET4.0E)',
                           'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) '
                           'Maxthon/4.0.6.2000 '
                           'Chrome/26.0.1410.43 Safari/537.1 ',
                           'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; SLCC2; .NET CLR '
                           '2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.2; '
                           '.NET4.0C; .NET4.0E; QQBrowser/7.3.9825.400)',
                           'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0 ',
                           'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) '
                           'Chrome/21.0.1180.92 Safari/537.1 LBBROWSER',
                           'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0; BIDUBrowser 2.x)',
                           'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) '
                           'Chrome/20.0.1132.11 TaoBrowser/3.0 Safari/536.11']
        jwc_header = {
            'User-Agent': head_user_agent[random.randrange(0, len(head_user_agent))],
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest;'
        }
    else:
        return jwc_header
