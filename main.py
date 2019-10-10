# coding=utf-8
__version__ = 12

import requests
import time
from threading import Thread

import choose_class
import config
import io_manage
import jwc_login

user_id = ""
user_pw = ""
keep_login_thread = False


def net_check():
    print('正在检查网络连通性...')
    request_result = requests.get(config.jwc_server)
    result = (int(request_result.status_code) == 200)
    request_result.close()
    return result


def login_jwc():
    global user_id, user_pw, keep_login_thread
    jwc_session = requests.Session()

    save_id = io_manage.read_data('user_id', False)
    save_pw = io_manage.read_data('user_pw', False)

    while True:
        if not (save_id and save_pw):
            print('\n请使用SSO信息门户密码登录教务系统（默认记住密码）')
            input_id = input('学号:')
            input_pw = input('密码:')
        else:
            input_id = save_id
            input_pw = save_pw
        if io_manage.input_yes_or_no('\n你确定使用' + input_id + '学号进行登录吗？(更改登陆账号或密码登陆请输入N或者n)', True):
            user_url = jwc_login.jwc_login(jwc_session, input_id, input_pw)
            if user_url:
                break
        else:
            save_id = False
            save_pw = False

    if user_url:
        user_id = input_id
        user_pw = input_pw

        io_manage.save_data(config.data_key_login_url, user_url)
        io_manage.save_data('user_id', input_id)
        io_manage.save_data('user_pw', input_pw)

        choose_class_list = {}

        choose_temp = io_manage.read_data(config.data_key_class_choose_list, choose_class_list)
        if len(choose_temp) != 0:
            if io_manage.input_yes_or_no('请问是否恢复上次抢课课程记录？（课程信息数据不同可能会导致选课失败）', False):
                choose_class_list = choose_temp
            else:
                if io_manage.input_yes_or_no('是否删除上次抢课课程记录？', True):
                    if io_manage.del_data(config.data_key_class_choose_list):
                        print('删除成功！\n')

        keep_login_thread = True
        t = KeepLoginThread(keep_login, args=(jwc_session,))
        t.setDaemon(True)
        t.start()

        choose_class.choose(jwc_session, user_url, choose_class_list)

        if t.isAlive():
            keep_login_thread = False

        jwc_login.jwc_logout(jwc_session)
        jwc_session.cookies.clear()
        jwc_session.close()
        user_id = ""
        user_pw = ""
    else:
        print('登录地址获取错误！')


def keep_login(jwc_session):
    time.sleep(30)
    while keep_login_thread and True:
        jwc_login.check_login(jwc_session, user_id, user_pw)
        time.sleep(60)


def logout_jwc():
    jwc_session = requests.Session()
    jwc_login.jwc_logout(jwc_session)
    print('已注销教务系统登陆！')


def main():
    print('南京审计大学教务系统 抢课脚本')
    print('%s:%d' % ('版本号', __version__))

    if net_check():
        while True:
            print('\n请输入数字进行操作：')
            print('1. 登陆教务系统')
            print('2. 注销教务系统')
            print('0. 退出')
            choose_int = io_manage.input_select_array(0, 3)
            if choose_int == 1:
                login_jwc()
            elif choose_int == 2:
                logout_jwc()
            elif choose_int == 0:
                break
    else:
        print('学校教务当前无法联通！请先检查你的网络设置！')
        input('\n<按任意键继续>\n')


class KeepLoginThread(Thread):
    def __init__(self, func, args=()):
        super(KeepLoginThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.func(*self.args)


if __name__ == '__main__':
    main()
    print('\n脚本正常运行结束')
