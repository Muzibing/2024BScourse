import os
import time
import json
import re
from urllib.parse import urlparse, urljoin, parse_qs, urlencode
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from django.http import JsonResponse

def fetchPriceData(shop, username):
    # 修复 URL，确保包含协议（http:// 或 https://）
    parsed_url = urlparse(shop)
    if not parsed_url.scheme:
        shop = urljoin("https:", shop)  # 默认使用 https
        parsed_url = urlparse(shop)

    # 重新编码查询参数，确保正确的 URL 格式
    query_params = parse_qs(parsed_url.query)
    encoded_query = urlencode(query_params, doseq=True)
    shop = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{encoded_query}"

    # 打印修复后的 URL
    print("修复后的 URL:", shop)

    # 设置 cookie 文件名
    cookie_file = f'cookie_manmanbuy_{username}.txt'

    # 配置 Chrome 浏览器选项
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    driver = webdriver.Chrome(options=chrome_options)

    # 自动执行代码使浏览器不再标记为自动化
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"}
    )

    # 登录万米比并获取 cookies
    def login_and_save_cookies(url, cookie_file):
        if not os.path.exists(cookie_file):
            driver.get(url)
            time.sleep(60)  # 手动登录
            cookies = driver.get_cookies()
            with open(cookie_file, 'w') as f:
                json.dump(cookies, f)
            print(f"Cookies 已保存到文件：{cookie_file}")
        else:
            print(f"{cookie_file} 已存在，跳过登录步骤。")
            driver.get(url)
            with open(cookie_file, 'r') as f:
                cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)

    # 登录万米比并保存 cookies
    login_and_save_cookies('https://home.manmanbuy.com/login.aspx', cookie_file)

    # 访问商品页面并获取实际 URL
    driver.get(shop)
    time.sleep(10)  # 等待页面加载
    shop = driver.current_url
    print("商品页面 URL:", shop)

    # 访问历史价格查询页面
    driver.get('http://tool.manmanbuy.com/HistoryLowest.aspx')
    time.sleep(2)

    # 查询历史价格数据
    search_box = driver.find_element(By.ID, "historykey")
    search_box.clear()
    search_box.send_keys(shop)  # 输入商品 URL
    time.sleep(2)

    search_button = driver.find_element(By.ID, "searchHistory")
    search_button.click()
    time.sleep(2)

    # 滚动页面加载所有数据
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)

    # 抓取价格数据
    data = []
    try:
        no_data_element = driver.find_element(By.XPATH, "//*[contains(text(), '暂未收录')]")
        if no_data_element:
            print("该商品未收录，停止操作。")
            driver.quit()
            return JsonResponse({'success': False, 'message': '暂未收录'})
    except NoSuchElementException:
        print("没有找到 '暂未收录' 元素，继续操作。")

    canvas = driver.find_element(By.ID, "container")
    canvas_location = canvas.location
    canvas_size = canvas.size

    for offset_x in range(-canvas_size['width'] // 2, canvas_size['width'] // 2, 36):
        ActionChains(driver).move_to_element(canvas).move_by_offset(offset_x, 0).perform()
        time.sleep(1)
        try:
            text_element = driver.find_element(By.XPATH,
                                               "//*[contains(@class, 'trend-box')]//div[contains(@style, 'position: absolute')]")
            text = text_element.text
            if text:
                first_space_index = text.find(' ')
                if first_space_index != -1:
                    date = text[:first_space_index].strip()
                    price_str = text[first_space_index + 1:].strip()
                    if "第一次收录" in date:
                        continue
                    price_match = re.search(r'\d+(\.\d+)?', price_str)
                    if price_match:
                        price = float(price_match.group())
                        data.append((date, price))
        except Exception as err:
            print(f"数据提取失败: {err}")

    # 关闭浏览器
    driver.quit()

    # 返回结果
    if not data:
        return JsonResponse({'success': False, 'message': '没有找到历史价格数据'})

    # 返回价格数据
    return JsonResponse({'success': True, 'data': data, 'message': ''})

if __name__ == '__main__':
    # 示例调用
    result = fetchPriceData("//item.taobao.com/item.htm?priceTId=215044dd17338263672054434e3914&utparam=%7B%22aplus_abtest%22%3A%223842a4336e380d3d1d08a37a21a1f5ce%22%7D&id=861425224960&ns=1&xxc=ad_ztc&skuId=5846512819113", 111)
    print(result)
