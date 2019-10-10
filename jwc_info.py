# coding=utf-8
import re

import requests
from bs4 import BeautifulSoup


def get_available_class(jwc_session, url):
    result = {}

    class_page_html = jwc_session.get(url)

    if type(class_page_html) is not requests.models.Response:
        return False

    soup = BeautifulSoup(class_page_html.text, "html.parser")

    result['term'] = get_class_term(class_page_html.text)
    result['limit'] = soup.find('span', id='LimitInfo').text
    result['select_style'] = soup.find('span', id='CourseSelectStyle').text
    result['s'] = soup.find('span', id='s').text
    result['e'] = soup.find('span', id='e').text
    result['start_date'] = soup.find('span', id='StartDate').text
    result['end_date'] = soup.find('span', id='EndDate').text
    result['submit'] = soup.find('a', text='提交选课信息')['href'][11:-2]
    result['rule'] = soup.find('span', id='rule').text

    class_page_html.close()

    key_list = []
    for th in soup.find('table', id='CourseList').find_all("th"):
        key_list.append(th.text)

    item_count = 0
    unavailable_class = False
    info = {}
    class_list = []
    info_start = False
    for td in soup.find('table', id='CourseList').find_all('td'):
        if '选课信息列表' in td.text:
            info_start = True
            continue
        if info_start:
            if (item_count == 0) and ('禁选' in td.text):
                unavailable_class = True

            if not unavailable_class:
                if item_count == 0:
                    for value in td.find_all('input'):
                        info['课程ID'] = value['value']
                info[key_list[item_count]] = td.text.replace('\r\n', '').strip()
                item_count = item_count + 1
                if item_count >= len(key_list):
                    class_list.append(info)
                    info = {}
                    item_count = 0
            else:
                item_count = item_count + 1
                if item_count >= len(key_list):
                    info = {}
                    item_count = 0
                    unavailable_class = False

    result['class_list'] = class_list
    return result


def get_class_term(html_text):
    pattern = re.compile(r'\(\"#Term\"\)\.text\(\'\d*\'\)')
    result = re.findall(pattern, html_text)
    if len(result) > 0:
        return result[0][16:-2]
    else:
        return False


def get_available_class_type(jwc_session, url):
    result = {}

    main_page_html = jwc_session.get(url)

    if type(main_page_html) is not requests.models.Response:
        return False

    soup = BeautifulSoup(main_page_html.text, "html.parser")

    main_page_html.close()

    found_class_start = False
    for span in soup.find_all("span"):
        if '在线选课' in span.text:
            found_class_start = True
            continue
        elif '考试报名' in span.text:
            break
        if found_class_start:
            if '补、退课申请及查询' in span.text:
                continue
            else:
                for a in span.find_all("a"):
                    url = a['href']
                    url = url[19:len(url) - 2]
                    result[span.text] = url

    if len(result) == 0:
        return False
    else:
        return result
