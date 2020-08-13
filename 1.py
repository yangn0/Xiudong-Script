import json
from selenium import webdriver
from pprint import pprint
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests
import time
import threading
import sys
import traceback


def Beijing_time():
    r = requests.get('https://www.baidu.com')
    t = time.strptime(r.headers['date'], '%a, %d %b %Y %H:%M:%S GMT')
    return time.mktime(t)+28800

# if(Beijing_time()-1595229814.799552>=86400*2):
#     input("测试期已过，请联系作者。")
#     sys.exit()


confirm_url = "https://wap.showstart.com/pages/order/activity/confirm/confirm?sequence=112533&ticketId=9e91b8d67588498ab759f8f3f5ae259a&ticketNum=1&ioswx=1&terminal=app&from=singlemessage&isappinstalled=0"
login_url = "https://wap.showstart.com/pages/passport/login/login?redirect=%2Fpages%2FmyHome%2FmyHome"


wait_time = input("等待时间（秒）：")

debug_flag = input("从post_list加载账号(2开启并继续添加 1开启 0关闭）：")
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
            # input("输入验证码后，按回车。")

            driver.get_log('performance')  # 清空

            b.click()

            time.sleep(1)

            logs = [json.loads(log['message'])['message'] for log in driver.get_log('performance') if (json.loads(log['message'])['message']['method'] == 'Network.requestWillBeSent' and 'order.json' in json.loads(
                log['message'])['message']['params']['request']['url']) or json.loads(log['message'])['message']['method'] == 'Network.requestWillBeSentExtraInfo']
            headers = dict()
            for i in logs:
                if i['method'] == 'Network.requestWillBeSentExtraInfo' and 'Accept' in i['params']['headers']:
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

mutex = threading.Lock()


def worker(i):
    while(1):
        try:
            r = requests.post(i[0], json=i[1], headers=i[2], timeout=(1, 0.1))
            d = json.loads(r.text)
            # d['msg']=='售票未开始'
            mutex.acquire()
            print(time.asctime(time.localtime(time.time())),
                  i[1]['telephone'], d['msg'])
            mutex.release()
            time.sleep(float(wait_time))
        except:
            mutex.acquire()
            print(time.asctime(time.localtime(time.time())),
                  i[1]['telephone'], '出错')
            mutex.release()
            time.sleep(float(wait_time))


if __name__ == '__main__':
    thread_l = list()
    for i in post_list:
        thread_l.append(threading.Thread(target=worker, args=(i,)))
    for i in thread_l:
        i.start()
    # for i in post_list:
    #     worker(i)
