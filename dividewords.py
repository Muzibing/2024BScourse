import jieba

# 商品名称示例
product_name = "小米RedmiNote11Pro智能手机128GB"

# 1. 精确模式分词（默认模式）
seg_list = jieba.cut(product_name, cut_all=False)  # cut_all=False 表示精确模式
print("精确模式分词结果：", "/ ".join(seg_list))

# 2. 全模式分词
seg_list_full = jieba.cut(product_name, cut_all=True)  # cut_all=True 表示全模式
print("全模式分词结果：", "/ ".join(seg_list_full))

# 3. 搜索引擎模式分词
seg_list_search = jieba.cut_for_search(product_name)  # 搜索引擎模式
print("搜索引擎模式分词结果：", "/ ".join(seg_list_search))

def jieba_cut(word):
    seg_list = jieba.cut(word, cut_all=False)
    print(type("/".join(seg_list)))
    return "/".join(seg_list)