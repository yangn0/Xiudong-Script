import gevent
from gevent import monkey
monkey.patch_all()

import traceback
import sys
import threading
import time
import requests
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from pprint import pprint
from selenium import webdriver
import json
import hashlib





confirm_url = "https://wap.showstart.com/pages/order/activity/confirm/confirm?sequence=112533&ticketId=9e91b8d67588498ab759f8f3f5ae259a&ticketNum=1&ioswx=1&terminal=app&from=singlemessage&isappinstalled=0"
login_url = "https://wap.showstart.com/pages/passport/login/login?redirect=%2Fpages%2FmyHome%2FmyHome"


wait_time = input("提前时间（秒）：")

debug_flag = input("从post_list加载账号(2开启并继续添加 1开启 0关闭）：")

start_time = input("开售时间（格式：2020 10 06 16 00 10）：")

DEBUG = int(debug_flag)

if DEBUG != 1:
    times = input("账号数量：")
    confirm_url = input("confirm_url：")
    caps = {
        'browserName': 'chrome',
        'loggingPrefs': {
            'browser': 'ALL',
            'driver': 'ALL',
            'performance': 'ALL',
        },
        'goog:chromeOptions': {
            'perfLoggingPrefs': {
                'enableNetwork': True,
            },
            'w3c': False,
        },
    }
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}
    options = webdriver.ChromeOptions()
    options.add_argument('log-level=3')
    options.add_argument('--window-size=400,700')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option(
        "mobileEmulation", {"deviceName": "Nexus 5"})
    driver = webdriver.Chrome(desired_capabilities=caps, options=options)

    if DEBUG == 2:
        with open('post_list.json', 'r') as f:
            post_list = json.load(f)
    else:
        post_list = []

    for n in range(int(times)):
        try:
            print("登录第%s个账号" % str(n+1))
            driver.get(login_url)
            WebDriverWait(driver, 1000).until(EC.title_is(u"我的"))
            driver.get(confirm_url)

            b = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.payBtn')))
            time.sleep(1)
            input("输入验证码或手机号后，按回车继续。")

            driver.get_log('performance')  # 清空

            b.click()

            time.sleep(1)

            logs = [json.loads(log['message'])['message'] for log in driver.get_log('performance') if (json.loads(log['message'])['message']['method'] == 'Network.requestWillBeSent' and 'order.json' in json.loads(
                log['message'])['message']['params']['request']['url']) or json.loads(log['message'])['message']['method'] == 'Network.requestWillBeSentExtraInfo']
            headers = dict()
            for i in logs:
                if i['method'] == 'Network.requestWillBeSentExtraInfo' and ('Accept' in i['params']['headers'] or 'accept' in i['params']['headers']):
                    for u in i['params']['headers']:
                        if ':' in u:
                            headers[u.strip(':')] = i['params']['headers'][u]
                        else:
                            headers[u] = i['params']['headers'][u]
                if i['method'] == 'Network.requestWillBeSent':
                    order_url = i['params']['request']['url']
                    postData = json.loads(i['params']['request']['postData'])
            post_list.append([order_url, postData, headers])
            driver.delete_all_cookies()
        except:
            print(traceback.format_exc())
            print("出错，跳过第%s个账号" % str(n+1))
    with open('post_list.json', 'w') as f:
        json.dump(post_list, f)

    try:
        driver.quit()
    except:
        pass
else:
    with open('post_list.json', 'r') as f:
        post_list = json.load(f)


def worker(i):
    n=10
    while(1):
        try:
            d = str(int(time.time()*1000))
            u = '/wap/order/order.json'
            st = i[2]['st_flpv']
            l = 'xVgXtOUSos6jzR3mqb4aLHYybqqPFFGfx12r'
            i[2]['r'] = str(int(time.time()*1000))
            i[2]['s'] = hashlib.md5((d+u+st+l).encode('utf8')).hexdigest()
            r = requests.post(i[0], json=i[1], headers=i[2],
                              timeout=(2, 0.001))
            d = json.loads(r.text)
            print(time.asctime(time.localtime(time.time())),time.time(),
                  i[1]['telephone'], '发包成功', d)
        except requests.exceptions.ReadTimeout:
            print(time.asctime(time.localtime(time.time())),time.time(),
                  i[1]['telephone'], '发包成功,不等待响应')
        except requests.exceptions.ConnectTimeout:
            print(time.asctime(time.localtime(time.time())),time.time(),
                  i[1]['telephone'], '请求超时')
        except:
            print(time.asctime(time.localtime(time.time())),time.time(),
                  i[1]['telephone'], traceback.format_exc())
        finally:
            n-=1
            if(n==0):
                print(time.asctime(time.localtime(time.time())),time.time(),
                  i[1]['telephone'], '已发包10次')
                break
            # time.sleep(float(wait_time))


if __name__ == '__main__':
    thread_l = list()
    for i in post_list:
        thread_l.append(gevent.spawn(worker, i=i))
    # 处理时间
    t1 = time.mktime(time.strptime(start_time, "%Y %m %d %H %M %S"))
    while(1):
        if(t1-time.time()<float(wait_time)):
            break

    gevent.joinall(thread_l)

    input()
    # for i in post_list:
    #     worker(i)
