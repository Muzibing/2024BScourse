from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from pyquery import PyQuery as pq

class JingDongOptions:
    def fetch_page_with_keyword(self,driver,keyword,page):
        base_url = "https://re.jd.com/search"
        url = f"{base_url}?keyword={keyword}&page={page}&enc=utf-8"
        driver.get(url)
        time.sleep(0.5)
        print(f"京东：已加载关键词'{keyword}'的第{page}页。")

    def search_goods(self,driver):
        page_source = driver.page_source
        doc = pq(page_source)

        product_divs = doc('.commodity_tit')
        pics = doc('.img_k')
        prices = doc('.price')
        jump_urls = doc('.li_cen_bot')

        goods_info = []

        if not product_divs:
            print("没有找到商品，请检查 HTML 结构和选择器。")
        else:
            for index,(product_div,pic,price,jump_url) in enumerate(
                zip(product_divs.items(),pics.items(),prices.items(),jump_urls.items()),1
            ):
                title = product_div.text()
                img_url = pic.attr('src')
                price.find('em').remove()
                price_ = price.text()
                # print(price_)
                jump_url_href = jump_url.find('a').attr('href')

                goods_info.append({
                    'title':title,
                    'image_url':img_url,
                    'price':price_,
                    'procity':'',
                    'jump_url':jump_url_href,
                    'from':'JingDong',
                    })
        return goods_info




def fetch_goods_by_creeper(keyword, pages=1):
    """
    根据关键词抓取商品信息，包括标题、图片链接、价格和促销信息，并返回结果。

    参数:
    keyword (str): 搜索关键词
    pages (int): 需要抓取的页数，默认为 1 页

    返回:
    list: 包含每个商品信息的字典列表，每个字典结构为：
        {
            'title': 商品标题,
            'image_url': 图片链接,
            'price': 完整价格（字符串，如 "99.99"）,
            'procity': 促销信息（字符串，如 "上海-北京"）
        }
    """
    # 设置无头模式（后台运行）
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=15360/2,8640/2")

    # 初始化 WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    # 存储所有页面的商品信息
    all_goods = []

    JingDong = JingDongOptions()
    for page in range(1, pages + 1):
        JingDong.fetch_page_with_keyword(driver,keyword,page)
        # print(JingDong.search_goods(driver))
        all_goods.extend(JingDong.search_goods(driver))

    # 关闭 WebDriver
    driver.quit()

    # print("typetype",type(all_goods))
    print("all_goods[0]: ",all_goods[0])
    return all_goods

if __name__ == '__main__':
    fetch_goods_by_creeper('电脑')
