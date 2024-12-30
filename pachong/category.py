import re
from collections import defaultdict

# 预定义大类和小类关键词
categories = {
    '电子产品': {
        '手机': ['手机', '智能手机', '手机壳', '手机配件'],
        '电脑': ['电脑', '笔记本', '台式机', '显示器', '键盘', '鼠标'],
        '电视': ['电视', '智能电视', 'LED电视', '液晶电视'],
        '耳机': ['耳机', '蓝牙耳机', '无线耳机']
    },
    '家居用品': {
        '家具': ['沙发', '床', '桌子', '椅子', '衣柜'],
        '厨房用品': ['锅', '刀具', '餐具', '微波炉'],
        '家装': ['灯具', '地毯', '窗帘'],
        '家纺': ['床单', '枕头', '被子', '床垫']
    },
    '服饰鞋包': {
        '服装': ['T恤', '外套', '裙子', '裤子', '衬衫'],
        '鞋子': ['运动鞋', '皮鞋', '拖鞋', '靴子'],
        '包包': ['背包', '手提包', '钱包', '旅行包'],
        '配饰': ['眼镜', '帽子', '围巾', '手表']
    },
    '食品饮料': {
        '饮料': ['饮料', '果汁', '矿泉水', '可乐', '咖啡'],
        '零食': ['饼干', '薯片', '糖果', '巧克力'],
        '保健食品': ['保健品', '维生素', '营养补充剂'],
        '生鲜': ['蔬菜', '水果', '肉类', '海鲜']
    }
}

# 分类函数
def classify_product(product_name):
    # 预处理商品名
    product_name = product_name.upper()
    product_name = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fa5]', ' ', product_name)  # 去除特殊字符

    category = None
    subcategory = None

    # 遍历大类
    for main_category, sub_categories in categories.items():
        # 遍历小类
        for sub_category, keywords in sub_categories.items():
            # 检查商品名中是否包含小类关键词
            for keyword in keywords:
                if keyword in product_name:
                    category = main_category
                    subcategory = sub_category
                    return category, subcategory
    if category == None:
        category = '其他'
    if subcategory == None:
        subcategory = '其他'
    return category, subcategory

def extract_specifications(product_name):
    specifications = {}

    # 尝试匹配并提取重量信息（支持 "斤"、"g"、"kg"）
    weight_match = re.sub(r'([0-9\.]+(?:斤|g|kg|ml|L|双|袋|套|公斤|千克))', lambda m: 'weight:' + m.group(0), product_name)
    if 'weight:' in weight_match:
        specifications['weight'] = weight_match.split('weight:')[1].split()[0]
        return specifications

    # 尝试匹配并提取尺寸信息（支持 "尺寸"、"大小" 等）
    size_match = re.sub(r'([0-9\.]+(?:cm|寸|m|毫米|厘米))', lambda m: 'size:' + m.group(0), product_name)
    if 'size:' in size_match:
        specifications['size'] = size_match.split('size:')[1].split()[0]
        return specifications

    # 尝试匹配并提取颜色信息（支持 "颜色"）
    color_match = re.sub(r'颜色[:：\s]*([a-zA-Z]+|[一二三四五六七八九十]+)', lambda m: 'color:' + m.group(1), product_name)
    if 'color:' in color_match:
        specifications['color'] = color_match.split('color:')[1].split()[0]
        return specifications

    return None

# # 示例输入
# product_name = "夏日清新组合糖棉绿色柔丽丝秋色扁豆100斤鲜切花艺术插花上海鲜花速递1g花"
# category, subcategory = classify_product(product_name)
# specifications = extract_specifications(product_name)
# print(f"商品类别: {category}, 小类: {subcategory}")
# print("商品规格",specifications)
