import re
from time import sleep
from lxml import etree
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager  # 使用 webdriver-manager 管理 chromedriver

class SuningProductSpider:
    def __init__(self, keyword):
        self.keyword = keyword
        option = Options()
        option.add_experimental_option('excludeSwitches', ['enable-automation'])  # 开启实验性功能
        option.add_experimental_option('prefs', {'profile.managed_default_content_settings.images': 2})  # 禁止图片加载
        option.add_argument('--headless')
        option.add_argument('--disable-gpu')  # 设置无头浏览器

        # 使用 webdriver-manager 管理 ChromeDriver，自动下载并配置
        service = Service(ChromeDriverManager().install())

        # 初始化 WebDriver
        self.bro = webdriver.Chrome(service=service, options=option)
        self.bro.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
          """
        })
        self.product_list = []  # 用于存储商品信息

    def get_comment_data(self):
        self.bro.get(f'https://search.suning.com/{self.keyword}/')

        # 等待总页数元素加载出来
        try:
            page_element = WebDriverWait(self.bro, 10).until(
                EC.presence_of_element_located((By.XPATH, '//span[@class="page-more"]'))
            )
            page = page_element.text  # 获取总页数
            page = re.findall(r'(\d+)', page)[0]
            print(f"{self.keyword} 苏宁 共检索到 {int(page)} 页数据")
        except Exception as e:
            print(f"未找到总页数元素：{e}")
            page = 1  # 如果没找到总页数，默认设置为1页

        self.start_page = 1
        self.end_page = int(page)  # 设定结束页数为实际抓取到的总页数

        for i in range(self.start_page, self.end_page + 1):
            sleep(4)
            self.bro.execute_script('window.scrollTo(0, document.body.scrollHeight)')  # 向下滑动一屏
            sleep(4)
            self.parser_product_data()
            sleep(4)
            if i < self.end_page:  # 确保不会在最后一页尝试翻页
                self.bro.find_element(By.XPATH, '//span[@class="page-more"]/input').send_keys(i + 1)  # 输入页数
                sleep(4)
                element = self.bro.find_element(By.XPATH, '//a[@class="page-more ensure"]')
                self.bro.execute_script("arguments[0].click();", element)  # 点击确认
        self.bro.quit()
        return self.product_list  # 返回商品列表

    def parser_product_data(self):
        html = etree.HTML(self.bro.page_source)
        li_list = html.xpath('//ul[@class="general clearfix"]/li')
        for li in li_list:
            product_info = {}
            try:
                product_info["name"] = "".join(li.xpath('.//div[@class="res-info"]/div[@class="title-selling-point"]/a[1]//text()')).replace("\n", "")
            except:
                product_info["name"] = ""
            try:
                product_info["price"] = "".join(li.xpath('.//div[@class="price-box"]/span[1]//text()')).replace("\n", "")
                product_info["price"] = product_info["price"][1:]  # 去掉 "¥" 符号
                product_info["price"] = product_info["price"].strip("到手价")
            except:
                product_info["price"] = ""
            try:
                product_info["image"] = "http:" + li.xpath('.//div[@class="img-block"]/a[1]/img/@src')[0]
            except:
                product_info["image"] = ""
            try:
                product_info["from"] = li.xpath('.//div[@class="store-stock"]/a[1]/text()')[0]
            except:
                product_info["from"] = ""
            try:
                detail_link = li.xpath('.//div[@class="res-info"]/div[@class="title-selling-point"]/a[1]/@href')[0]
                product_info["link"] = detail_link if "http" in detail_link else "http:" + detail_link
            except:
                product_info["link"] = ""
            self.product_list.append(product_info)  # 添加到商品列表中

        if len(self.product_list) >= 20:
            self.product_list = self.product_list[:20]  # 限制商品列表最多20个

if __name__ == '__main__':
    spider = SuningProductSpider('沙栾')  # 传入要搜索的关键字
    products = spider.get_comment_data()
    print(products[0])  # 打印第一个商品的信息
