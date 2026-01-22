函数
====

定义函数
--------

::

    def greet(name):
        """问候函数（这是文档字符串）"""
        return f"Hello, {name}!"
    
    result = greet("Tom")  # "Hello, Tom!"

::

    # 无返回值
    def say_hello():
        print("Hello!")
    
    # 多返回值
    def get_point():
        return 1, 2       # 返回元组
    
    x, y = get_point()    # 解包


参数类型
--------

**位置参数**::

    def add(a, b):
        return a + b
    
    add(1, 2)             # 按位置传参

**默认参数**::

    def power(x, n=2):
        return x ** n
    
    power(3)              # 9 使用默认值
    power(3, 3)           # 27

**关键字参数**::

    def info(name, age):
        print(f"{name}, {age}")
    
    info(age=18, name="Tom")  # 按名称传参

**可变位置参数 \*args**::

    def add(*args):
        return sum(args)
    
    add(1, 2, 3)          # 6
    add(1, 2, 3, 4, 5)    # 15

**可变关键字参数 \*\*kwargs**::

    def info(**kwargs):
        for k, v in kwargs.items():
            print(f"{k}: {v}")
    
    info(name="Tom", age=18)


Lambda 表达式
-------------

匿名函数，用于简单的单行函数::

    square = lambda x: x ** 2
    square(5)             # 25
    
    add = lambda a, b: a + b
    add(1, 2)             # 3

常用于排序等场景::

    students = [("Tom", 85), ("Jerry", 92)]
    students.sort(key=lambda x: x[1])  # 按成绩排序


常用内置函数
------------

**类型相关**::

    type(obj)             # 返回类型
    isinstance(obj, int)  # 判断类型
    id(obj)               # 返回对象id

**数学相关**::

    abs(-5)               # 5 绝对值
    max(1, 2, 3)          # 3 最大值
    min(1, 2, 3)          # 1 最小值
    sum([1, 2, 3])        # 6 求和
    pow(2, 3)             # 8 幂运算
    round(3.14159, 2)     # 3.14 四舍五入
    divmod(7, 3)          # (2, 1) 商和余数

**序列相关**::

    len(obj)              # 长度
    range(5)              # 0,1,2,3,4
    sorted([3, 1, 2])     # [1, 2, 3] 排序（返回新列表）
    reversed([1, 2, 3])   # 反转迭代器
    enumerate(list)       # 带索引遍历
    zip(list1, list2)     # 并行遍历
    map(func, list)       # 映射
    filter(func, list)    # 过滤
    all([True, True])     # True 全为真
    any([False, True])    # True 有一个真

**其他**::

    print(*args)          # 打印输出
    input(prompt)         # 读取输入
    open(file)            # 打开文件
    help(obj)             # 查看帮助
    dir(obj)              # 查看属性和方法

