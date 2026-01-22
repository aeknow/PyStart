数据类型
========

字符串 str
----------

::

    s = "Hello"
    s = 'Hello'          # 单引号也可以
    s = """多行
    字符串"""

**常用方法**::

    s.upper()            # "HELLO" 转大写
    s.lower()            # "hello" 转小写
    s.strip()            # 去除首尾空格
    s.replace("H", "J")  # "Jello" 替换
    s.split(",")         # 按逗号分割成列表
    s.join(["a","b"])    # "aHb" 用s连接列表
    s.startswith("He")   # True 是否以...开头
    s.endswith("lo")     # True 是否以...结尾
    s.find("ll")         # 2 查找子串位置
    s.count("l")         # 2 统计出现次数
    len(s)               # 5 字符串长度

**格式化**::

    f"Hi, {name}"        # f-string (推荐)
    "Hi, {}".format(name) # format方法
    "Hi, %s" % name      # % 格式化


列表 list
---------

::

    arr = [1, 2, 3]
    arr = list("abc")    # ['a', 'b', 'c']

**常用方法**::

    arr.append(4)        # 末尾添加 [1,2,3,4]
    arr.extend([5,6])    # 扩展列表 [1,2,3,4,5,6]
    arr.insert(0, 0)     # 指定位置插入
    arr.pop()            # 删除并返回末尾元素
    arr.pop(0)           # 删除并返回指定位置元素
    arr.remove(2)        # 删除第一个值为2的元素
    arr.clear()          # 清空列表
    arr.index(2)         # 查找元素位置
    arr.count(2)         # 统计元素出现次数
    arr.sort()           # 排序（原地）
    arr.reverse()        # 反转（原地）
    arr.copy()           # 浅拷贝
    len(arr)             # 列表长度

**索引和切片**::

    arr[0]               # 第一个元素
    arr[-1]              # 最后一个元素
    arr[1:3]             # 切片 [1,2] (不含3)
    arr[::2]             # 步长为2 [0,2,4...]
    arr[::-1]            # 反转列表


元组 tuple
----------

元组是不可变的列表::

    t = (1, 2, 3)
    t = 1, 2, 3          # 括号可省略
    t[0]                 # 访问元素
    a, b, c = t          # 解包


字典 dict
---------

::

    d = {"name": "Tom", "age": 18}
    d = dict(name="Tom", age=18)

**常用方法**::

    d["name"]            # "Tom" 获取值（键不存在会报错）
    d.get("name")        # "Tom" 安全获取
    d.get("x", 0)        # 0 不存在返回默认值
    d["score"] = 100     # 添加/修改
    del d["age"]         # 删除键
    d.pop("age")         # 删除并返回值
    d.keys()             # 所有键
    d.values()           # 所有值
    d.items()            # 所有键值对
    d.update({"a": 1})   # 批量更新
    "name" in d          # True 判断键是否存在
    len(d)               # 字典长度


集合 set
--------

集合是无序不重复的元素集::

    s = {1, 2, 3}
    s = set([1, 2, 2, 3]) # {1, 2, 3} 去重

**常用方法**::

    s.add(4)             # 添加元素
    s.remove(1)          # 删除元素（不存在会报错）
    s.discard(1)         # 删除元素（不存在不报错）
    s1 | s2              # 并集
    s1 & s2              # 交集
    s1 - s2              # 差集


类型转换
--------

::

    int("123")           # 123 字符串转整数
    float("3.14")        # 3.14 字符串转浮点数
    str(123)             # "123" 转字符串
    list("abc")          # ['a','b','c']
    tuple([1,2,3])       # (1,2,3)
    set([1,2,2])         # {1,2}
    dict([("a",1)])      # {"a": 1}
    bool(1)              # True
    bool(0)              # False
    bool("")             # False
    bool([])             # False

