文件与异常
==========

文件操作
--------

**读取文件**::

    # 推荐：使用 with 语句（自动关闭文件）
    with open("file.txt", "r", encoding="utf-8") as f:
        content = f.read()       # 读取全部内容
    
    with open("file.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()    # 读取所有行（列表）
    
    with open("file.txt", "r", encoding="utf-8") as f:
        for line in f:           # 逐行读取（省内存）
            print(line.strip())

**写入文件**::

    # w 模式：覆盖写入
    with open("file.txt", "w", encoding="utf-8") as f:
        f.write("Hello\n")
        f.write("World\n")
    
    # 写入多行
    with open("file.txt", "w", encoding="utf-8") as f:
        lines = ["line1\n", "line2\n", "line3\n"]
        f.writelines(lines)

**追加内容**::

    # a 模式：追加写入
    with open("file.txt", "a", encoding="utf-8") as f:
        f.write("追加的内容\n")

**文件模式**::

    "r"   只读（默认）
    "w"   写入（覆盖）
    "a"   追加
    "rb"  二进制读
    "wb"  二进制写


路径操作
--------

::

    import os
    
    os.getcwd()              # 当前工作目录
    os.chdir("/path")        # 切换目录
    os.listdir(".")          # 列出目录内容
    os.mkdir("newdir")       # 创建目录
    os.makedirs("a/b/c")     # 创建多级目录
    os.remove("file.txt")    # 删除文件
    os.rmdir("emptydir")     # 删除空目录
    os.rename("old", "new")  # 重命名

::

    import os.path
    
    os.path.exists("a.txt")  # 路径是否存在
    os.path.isfile("a.txt")  # 是否是文件
    os.path.isdir("mydir")   # 是否是目录
    os.path.join("a", "b")   # 拼接路径 "a/b"
    os.path.split("/a/b.txt") # ('/a', 'b.txt')
    os.path.splitext("a.txt") # ('a', '.txt')
    os.path.basename("/a/b") # "b"
    os.path.dirname("/a/b")  # "/a"
    os.path.abspath(".")     # 绝对路径


异常处理
--------

**基本语法**::

    try:
        result = 10 / 0
    except ZeroDivisionError:
        print("除数不能为零")

**捕获多种异常**::

    try:
        # 可能出错的代码
        pass
    except ValueError:
        print("值错误")
    except TypeError:
        print("类型错误")
    except Exception as e:
        print(f"其他错误: {e}")

**完整结构**::

    try:
        f = open("file.txt")
        content = f.read()
    except FileNotFoundError:
        print("文件不存在")
    except Exception as e:
        print(f"发生错误: {e}")
    else:
        print("没有异常时执行")
    finally:
        print("总是执行（通常用于清理）")

**主动抛出异常**::

    if age < 0:
        raise ValueError("年龄不能为负数")


常见异常类型
------------

::

    Exception           # 所有异常的基类
    ValueError          # 值错误
    TypeError           # 类型错误
    IndexError          # 索引越界
    KeyError            # 键不存在
    FileNotFoundError   # 文件不存在
    ZeroDivisionError   # 除以零
    AttributeError      # 属性错误
    ImportError         # 导入错误
    NameError           # 名称未定义

