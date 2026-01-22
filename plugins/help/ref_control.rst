流程控制
========

条件判断 if
-----------

::

    if score >= 90:
        print("优秀")
    elif score >= 60:
        print("及格")
    else:
        print("不及格")

**单行写法**::

    result = "及格" if score >= 60 else "不及格"


for 循环
--------

::

    # 遍历范围
    for i in range(5):       # 0,1,2,3,4
        print(i)
    
    for i in range(1, 6):    # 1,2,3,4,5
        print(i)
    
    for i in range(0, 10, 2): # 0,2,4,6,8
        print(i)

::

    # 遍历列表
    for item in [1, 2, 3]:
        print(item)
    
    # 带索引遍历
    for i, item in enumerate(["a", "b", "c"]):
        print(i, item)  # 0 a, 1 b, 2 c

::

    # 遍历字典
    for key in d:
        print(key)
    
    for key, value in d.items():
        print(key, value)

::

    # 并行遍历
    for a, b in zip(list1, list2):
        print(a, b)


while 循环
----------

::

    i = 0
    while i < 5:
        print(i)
        i += 1

::

    # 无限循环
    while True:
        cmd = input("> ")
        if cmd == "quit":
            break


循环控制
--------

::

    break       # 跳出整个循环
    continue    # 跳过本次，继续下一次

::

    # break 示例
    for i in range(10):
        if i == 5:
            break       # 到5就停止
        print(i)        # 输出 0,1,2,3,4

::

    # continue 示例
    for i in range(5):
        if i == 2:
            continue    # 跳过2
        print(i)        # 输出 0,1,3,4


列表推导式
----------

::

    # 基本形式
    squares = [x**2 for x in range(5)]
    # [0, 1, 4, 9, 16]
    
    # 带条件
    evens = [x for x in range(10) if x % 2 == 0]
    # [0, 2, 4, 6, 8]
    
    # 嵌套
    pairs = [(x, y) for x in [1,2] for y in [3,4]]
    # [(1,3), (1,4), (2,3), (2,4)]


字典推导式
----------

::

    d = {x: x**2 for x in range(5)}
    # {0: 0, 1: 1, 2: 4, 3: 9, 4: 16}

