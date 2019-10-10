# coding=utf-8
import time
from bs4 import BeautifulSoup

import config
import io_manage


def jwc_login(jwc_session, user_id, user_pw, re_login=False):
    try:
        html_jwc_login = jwc_session.get(config.jwc_server_single_login, timeout=60)
        post_form = get_post_form(html_jwc_login.text, user_id, user_pw)

        html_jwc_login_result = jwc_session.post(config.jwc_server_single_login, post_form, timeout=15)
        result = html_jwc_login_result.text
    except TimeoutError:
        if re_login:
            print("登陆超时！")
        return False
    except:
        if re_login:
            print("登陆错误！")
        return False
    else:
        if str.startswith(result, '当前你已经登录'):
            if re_login or io_manage.input_yes_or_no('你已经在这台设备上登录了教务系统，是否尝试注销后重新登录？', True):
                jwc_logout(jwc_session)
                time.sleep(1)
                return jwc_login(jwc_session, user_id, user_pw)
        elif '请勿输入非法字符' in result:
            if re_login or io_manage.input_yes_or_no('教务系统错误，是否尝试重新登录？', True):
                return jwc_login(jwc_session, user_id, user_pw)
        elif '密码错误' in result:
            if not re_login:
                print('用户名或者密码错误，请重新登录！')
        else:
            return html_jwc_login_result.url

        return False


def get_post_form(html_content, user_id, user_pw):
    form = {'username': user_id, 'password': user_pw}

    soup = BeautifulSoup(html_content, "html.parser")
    for node in soup.find_all('input'):
        value = node.get('value')
        name = node.get('name')
        if name == 'lt' or name == 'execution' or name == '_eventId' or name == 'useVCode' or name == 'isUseVCode' or \
                name == 'sessionVcode' or name == 'errorCount':
            form[name] = value

    return form


def jwc_logout(jwc_session):
    jwc_session.get(config.jwc_server + 'LoginOut.aspx')
    jwc_session.cookies.clear()


def check_login(jwc_session, user_id, user_pw):
    content = jwc_session.get(config.jwc_keep_login_url)
    if not (("用户编号" in content.text) and ("更改密码" in content.text)):
        if user_id != "" and user_pw != "":
            if not jwc_login(jwc_session, user_id, user_pw, True):
                print("\n你可能已经掉线，网络连接检测失败，请退出脚本后重新登录！\n")
        else:
            print("\n你可能已经掉线，网络连接检测失败，请退出脚本后重新登录！\n")
