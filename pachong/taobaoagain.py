import time
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def get_taobao_price(link):
    # 设置 Chrome 配置
    options = Options()
    options.add_argument('--headless')  # 无头模式，不显示浏览器界面
    options.add_argument('--disable-gpu')  # 禁用 GPU 加速
    options.add_argument('start-maximized')  # 启动时最大化
    options.add_argument('disable-infobars')  # 禁用自动化提示
    options.add_argument('--no-sandbox')  # 无沙箱模式

    driver = None  # 定义driver为None，避免未定义错误

    try:
        # 使用 Service 来设置 chromedriver 路径
        service = Service(ChromeDriverManager().install())

        # 启动 WebDriver (Chrome 浏览器)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(link)  # 打开淘宝商品链接

        # 等待页面加载
        time.sleep(5)  # 等待 JavaScript 渲染完成，确保价格元素加载

        # 查找价格元素
        price_span = driver.find_element(By.CSS_SELECTOR, 'span.text--fZ9NUhyQ')

        # 获取价格文本
        price = price_span.text.strip()
        return price

    except Exception as e:
        return f"请求错误: {e}"

    finally:
        # 确保关闭浏览器
        if driver:
            driver.quit()

# 测试链接（请替换为实际淘宝商品链接）
taobao_link = "https://item.taobao.com/item.htm?priceTId=213e379417337502177346058ec0b0&utparam=%7B%22aplus_abtest%22%3A%22baee2dfc081299f262d6b8d8d595a960%22%7D&id=809091464455&ns=1&xxc=ad_ztc&skuId=5665425467315"
price = get_taobao_price(taobao_link)
print(f"商品价格: {price}")
