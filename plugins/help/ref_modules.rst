常用模块
========

json - JSON处理
---------------

::

    import json
    
    # Python对象 → JSON字符串
    data = {"name": "Tom", "age": 18}
    json_str = json.dumps(data)
    json_str = json.dumps(data, ensure_ascii=False, indent=2)  # 中文+美化
    
    # JSON字符串 → Python对象
    obj = json.loads('{"name": "Tom"}')
    
    # 写入JSON文件
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 读取JSON文件
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)


datetime - 日期时间
-------------------

::

    from datetime import datetime, timedelta
    
    # 当前时间
    now = datetime.now()
    
    # 格式化输出
    now.strftime("%Y-%m-%d %H:%M:%S")  # "2024-01-15 14:30:00"
    now.strftime("%Y年%m月%d日")        # "2024年01月15日"
    
    # 解析字符串
    dt = datetime.strptime("2024-01-15", "%Y-%m-%d")
    
    # 时间计算
    tomorrow = now + timedelta(days=1)
    yesterday = now - timedelta(days=1)
    
    # 获取属性
    now.year, now.month, now.day
    now.hour, now.minute, now.second

**格式符号**::

    %Y  四位年份  2024
    %m  月份      01-12
    %d  日期      01-31
    %H  小时      00-23
    %M  分钟      00-59
    %S  秒        00-59


random - 随机数
---------------

::

    import random
    
    random.random()          # 0-1 随机小数
    random.randint(1, 10)    # 1-10 随机整数（含两端）
    random.uniform(1, 10)    # 1-10 随机浮点数
    random.choice([1,2,3])   # 随机选择一个
    random.choices([1,2,3], k=2)  # 随机选择k个（可重复）
    random.sample([1,2,3], k=2)   # 随机选择k个（不重复）
    random.shuffle(arr)      # 打乱顺序（原地修改）


re - 正则表达式
---------------

::

    import re
    
    # 查找
    re.search(r'\d+', 'abc123def')  # 找到 '123'
    re.findall(r'\d+', 'a1b2c3')    # ['1', '2', '3']
    
    # 替换
    re.sub(r'\d+', 'X', 'a1b2')     # 'aXbX'
    
    # 分割
    re.split(r'[,;]', 'a,b;c')      # ['a', 'b', 'c']
    
    # 匹配
    if re.match(r'^\d+$', '123'):
        print("纯数字")

**常用模式**::

    \d      数字 [0-9]
    \w      单词字符 [a-zA-Z0-9_]
    \s      空白字符
    .       任意字符
    *       0次或多次
    +       1次或多次
    ?       0次或1次
    ^       开头
    $       结尾
    [abc]   字符集合
    (...)   分组


time - 时间
-----------

::

    import time
    
    time.time()              # 当前时间戳（秒）
    time.sleep(1)            # 暂停1秒
    time.strftime("%Y-%m-%d") # 格式化当前时间


collections - 集合扩展
----------------------

::

    from collections import Counter, defaultdict, deque
    
    # Counter - 计数器
    c = Counter("hello")     # {'l': 2, 'h': 1, 'e': 1, 'o': 1}
    c.most_common(2)         # 最常见的2个
    
    # defaultdict - 带默认值的字典
    d = defaultdict(list)
    d["key"].append(1)       # 自动创建空列表
    
    # deque - 双端队列
    q = deque([1, 2, 3])
    q.append(4)              # 右侧添加
    q.appendleft(0)          # 左侧添加
    q.pop()                  # 右侧弹出
    q.popleft()              # 左侧弹出


math - 数学
-----------

::

    import math
    
    math.pi                  # 3.14159...
    math.e                   # 2.71828...
    math.sqrt(16)            # 4.0 平方根
    math.pow(2, 3)           # 8.0 幂
    math.ceil(3.2)           # 4 向上取整
    math.floor(3.8)          # 3 向下取整
    math.log(10)             # 自然对数
    math.log10(100)          # 2.0 以10为底

