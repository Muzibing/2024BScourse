from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from pyquery import PyQuery as pq

class TaoBaoOptions:
    def fetch_page_with_keyword(self,driver,keyword,page):
        """根据页数请求页面并加载"""
        base_url = "https://uland.taobao.com/sem/tbsearch"
        url = f"{base_url}?clk1=b27114e13eaf50a5b4b3472c3265ec77&keyword={keyword}&localImgKey=&page={page}&q=&refpid=mm_2898300158_3078300397_115665800437&tab=all&upsId=b27114e13eaf50a5b4b3472c3265ec77"
        driver.get(url)
        time.sleep(0.5)  # 等待页面加载完成
        print(f"淘宝联盟：已加载关键词 '{keyword}' 的第 {page} 页。")

    def search_goods(self,driver):
        """抓取商品的标题、图片链接、价格和促销信息"""
        page_source = driver.page_source
        doc = pq(page_source)

        # 查找商品信息
        product_divs = doc('.Title--title--jCOPvpf')
        pics = doc('.MainPic--mainPicWrapper--iv9Yv90 img')
        price_ints = doc('.Price--priceInt--ZlsSi_M')
        price_floats = doc('.Price--priceFloat--h2RR0RK')
        procity_elements = doc('.Price--procity--_7Vt3mX')
        jump_urls = doc('.Card--doubleCardWrapper--L2XFE73')

        # 用于存储最终商品信息
        goods_info = []

        if not product_divs:
            print("没有找到商品，请检查 HTML 结构和选择器。")
        else:
            for index, (product_div, pic, price_int, price_float, jump_url) in enumerate(
                zip(product_divs.items(), pics.items(), price_ints.items(), price_floats.items(), jump_urls.items()), 1
            ):
                # 获取商品标题
                title = " ".join(span.text() for span in product_div.find('span').items())

                # 获取图片链接
                img_url = pic.attr('src') or pic.attr('data-src')  # 兼容懒加载的 data-src

                jump_url_href = jump_url.attr('href')

                # 组合价格
                price = f"{price_int.text()}{price_float.text()}"

                # 组合促销信息
                procity_index = (index - 1) * 2  # 每个商品有两个procities
                procity = (
                    f"{procity_elements.eq(procity_index).text()}-{procity_elements.eq(procity_index + 1).text()}"
                    if procity_elements.eq(procity_index) and procity_elements.eq(procity_index + 1)
                    else ""
                )

                # 添加到商品信息列表
                goods_info.append({
                    'title': title,
                    'image_url': img_url,
                    'price': price,
                    'procity': procity,
                    'jump_url': jump_url_href,
                    'from': 'UlandTaoBao',
                })

        return goods_info

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

        # category_elements = doc('a[clstag="shangpin|keycount|product|mbNav-1"]')

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
                # category_element = category_element.text()

                goods_info.append({
                    'title':title,
                    'image_url':img_url,
                    'price':price_,
                    'procity':'',
                    'jump_url':jump_url_href,
                    'from':'JingDong'
                    # 'category_elements':category_element
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

    print("淘宝and京东初始化完成")
    TaoBao = TaoBaoOptions()
    # 存储所有页面的商品信息
    all_goods = []
    for page in range(1, pages + 1):
        TaoBao.fetch_page_with_keyword(driver,keyword,page)
        # print(TaoBao.search_goods(driver))
        all_goods.extend(TaoBao.search_goods(driver))

    if(len(all_goods) >= 20):
        all_goods = all_goods[:20]


    JingDong = JingDongOptions()
    for page in range(1, pages + 1):
        JingDong.fetch_page_with_keyword(driver,keyword,page)
        # print(JingDong.search_goods(driver))
        all_goods.extend(JingDong.search_goods(driver))

    if(len(all_goods) >= 40):
        all_goods = all_goods[:40]

    # 关闭 WebDriver
    driver.quit()

    # print("typetype",type(all_goods))
    print("all_goods[0]: ",all_goods[0],"all_goods[len-1]:",all_goods[-1])
    return all_goods

# if __name__ == '__main__':
#     fetch_goods_by_creeper('电脑')
