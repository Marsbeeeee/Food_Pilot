# -*- coding: utf-8 -*-
"""
真实用户问题小范围回归数据集。

用途：验证「推荐像建议、估算像估算」——高频问题能被正确分到两大核心意图。
来源：产品规范书典型示例 + 常见真实问法。
"""

RECOMMENDATION = "meal_recommendation"
ESTIMATE = "meal_estimate"

# (用户输入, 期望意图)
# 推荐意图：用户想知道「该怎么选 / 换什么更好 / 哪个更适合我」
REAL_USER_CASES = [
    # ----- 推荐意图：推荐吃什么、选哪个、换什么、怎么优化 -----
    ("今天午饭推荐吃什么？", RECOMMENDATION),
    ("帮我推荐一个减脂晚餐", RECOMMENDATION),
    ("早餐想吃得清淡一点，推荐一下", RECOMMENDATION),
    ("我训练后适合吃什么？", RECOMMENDATION),
    ("推荐训练后吃什么", RECOMMENDATION),
    ("汉堡和鸡肉沙拉哪个更适合我今天晚饭？", RECOMMENDATION),
    ("米饭和红薯哪个更适合减脂期？", RECOMMENDATION),
    ("麻辣烫和黄焖鸡哪个更值得选？", RECOMMENDATION),
    ("奶茶想换掉，有什么更好的替代？", RECOMMENDATION),
    ("炸鸡想换成相对健康一点的，可以换什么？", RECOMMENDATION),
    ("我对花生过敏，晚餐推荐吃什么？", RECOMMENDATION),
    ("这份午餐怎么优化会更适合控卡？", RECOMMENDATION),
    ("外卖里怎么选会更稳妥一点？", RECOMMENDATION),
    ("今天晚饭吃什么比较合适？", RECOMMENDATION),
    ("帮我推荐减脂午餐", RECOMMENDATION),
    ("午饭吃什么比较合适？", RECOMMENDATION),
    ("帮我推荐一个更轻一点的晚餐", RECOMMENDATION),
    ("  帮我推荐一下   今天晚饭吃什么  ", RECOMMENDATION),
    ("帮我选个低卡的", RECOMMENDATION),
    ("沙拉和轻食哪个更好", RECOMMENDATION),
    ("鸡胸肉和鸡腿差别是什么，哪个更适合减脂晚餐？", RECOMMENDATION),
    ("炸鸡想换成更健康的，为什么这么换更合适？", RECOMMENDATION),
    ("米饭还是红薯更适合减脂吗？", RECOMMENDATION),
    ("奶茶有没有更健康的平替？", RECOMMENDATION),
    # ----- 估算意图：描述一餐 + 问热量/营养/大概多少 -----
    ("这份鸡胸肉沙拉大概多少热量？", ESTIMATE),
    ("一碗牛肉面大概多少卡？", ESTIMATE),
    ("我中午吃了两个包子一杯豆浆，大概多少热量？", ESTIMATE),
    ("这碗麻辣烫大概有多少蛋白质和碳水？", ESTIMATE),
    ("一个麦香鸡套餐大概多少热量？", ESTIMATE),
    ("我刚吃的寿司拼盘营养大概怎么样？", ESTIMATE),
    ("这顿饭的脂肪和碳水大概各有多少？", ESTIMATE),
    ("一份番茄炒蛋加一碗米饭大概多少卡？", ESTIMATE),
    ("我晚饭吃了炒面和可乐，热量大概多少？", ESTIMATE),
    ("这份轻食碗的营养结构大概是什么？", ESTIMATE),
    ("这个三明治大概有多少蛋白质？", ESTIMATE),
    ("我今天这餐大概吃了多少热量和营养？", ESTIMATE),
    ("汉堡和沙拉哪个好，卡路里分别是多少？", ESTIMATE),
    ("这份餐大概多少热量？", ESTIMATE),
    ("一碗鸡胸肉沙拉加半个牛油果", ESTIMATE),
    ("这碗麻辣烫大概有多少蛋白质和碳水？", ESTIMATE),
    ("两根玉米一个水煮蛋", ESTIMATE),
    ("一杯拿铁一个可颂", ESTIMATE),
    ("一份凉皮加肉夹馍", ESTIMATE),
]
