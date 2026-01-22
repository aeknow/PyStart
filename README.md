# PyStart IDE

> **给 Python 初学者的第一个编程环境**
> 
> 不需要配置环境，不需要看教程，解压即用。

---

## 这是什么？

PyStart 是一款专门为 **Python 初学者** 打造的编程工具（学名叫 IDE，集成开发环境）。

无论你是学生、研究人员、还是对编程感兴趣的任何人，只要你想用 Python 做点什么，PyStart 就是一个不错的起点。

**它基于 [Thonny](https://thonny.org)**——一款由爱沙尼亚塔尔图大学开发的教学用 Python IDE，我们在此基础上进行了本土化改进和功能增强。

---

## 为什么选择 PyStart？

| 特点 | 说明 |
|------|------|
| ✅ **开箱即用** | 下载解压，双击运行，没有“安装 Python”这一步 |
| ✅ **中文界面** | 菜单、提示信息都是中文，降低学习门槛 |
| ✅ **预装 AI 库** | 内置 openai 等库，紧跟大模型时代潮流 |
| ✅ **AI 助手** | 内置 AI 对话功能，配置后遇到问题可以直接问 |
| ✅ **可视化调试** | 能看到程序一步步执行，变量怎么变化 |

> 💡 **一句话总结**：别的 IDE 是给程序员用的，PyStart 是给"想使用编程工具的人"用的。

---

## 功能一览

| 功能 | 描述 | 适合场景 |
|------|------|----------|
| 🎯 **简洁界面** | 没有让人眼花缭乱的按钮 | 专注学习，不分心 |
| 🐛 **单步调试** | 点一下执行一行，观察变量变化 | 理解程序运行逻辑 |
| 📊 **变量面板** | 实时显示所有变量的值和类型 | 调试、学习 |
| 💡 **代码补全** | 输入几个字母自动提示 | 减少拼写错误 |
| 🎨 **语法高亮** | 不同代码用不同颜色标注 | 更容易阅读 |
| 📦 **包管理器** | 图形界面安装第三方库 | 告别命令行恐惧 |
| 🤖 **AI 助手** | 代码看不懂？选中后问 AI | 24小时答疑 |
| 🌐 **中文支持** | 完整汉化 | 母语学习更轻松 |
| 🔑 **去中心化身份** | 助记词管理身份，支持签名/加密 | 学习密码学、身份认证 |

> 📖 **详细了解**：[去中心化用户系统文档](USER_SYSTEM.md)

---

## 安装方式

### 方式一：绿色便携版（推荐新手）

1. 下载压缩包
2. 解压到任意目录（建议路径不要有中文）
3. 双击 `PyStart.bat`
4. 完成 ✅

> 这个版本自带 Python，不需要额外安装任何东西。  
> 可以放在 U 盘里随身携带。

### 方式二：pip 安装（适合已有 Python 环境）

```bash
pip install pystart
```

安装后，在命令行输入 `pystart` 或 `python -m pystart` 启动。

---

## 快速开始：5 分钟写出第一个程序

### Hello World

```python
print("Hello, PyStart!")
print("我的第一个 Python 程序")
```

点击 ▶️ 按钮运行，下方 Shell 窗口会显示输出结果。



### 调用 AI 大模型

```python
from openai import OpenAI

client = OpenAI(
    api_key="你的API-KEY,注册即可免费申请使用",
    base_url="https://api.longcat.chat/openai"  # 以美团LongCat为例
)

response = client.chat.completions.create(
    model="LongCat-Flash-Chat",
    messages=[{"role": "user", "content": "介绍下你自己"}],
    stream=True  # 启用流式输出
)

for chunk in response:
    content = chunk.choices[0].delta.content
    if content is not None:
        print(content, end="", flush=True)
```

> 💡 有了 PyStart 预装的 `openai` 库，你可以立刻开始探索 AI 编程。

### 来个小游戏

```python
import random

answer = random.randint(1, 100)
print("我想了一个1到100之间的数字，猜猜看？")

while True:
    guess = int(input("你的猜测: "))
    if guess < answer:
        print("太小了！")
    elif guess > answer:
        print("太大了！")
    else:
        print("恭喜你，猜对了！🎉")
        break
```

---

## 预装库清单（标准版）

PyStart 标准版已经预装了这些常用库，**无需额外安装，开箱即用**：

### 🤖 AI 与大模型（⭐ 紧跟时代热点）

| 库名 | 版本 | 用途 |
|------|------|------|
| openai | 2.15 | 调用通义千问、DeepSeek、 ChatGPT 等 AI 接口 |
| pydantic | 2.12 | 数据结构定义，AI 应用开发必备 |
| httpx | 0.28 | 现代化 HTTP 客户端，支持异步请求 |

> 💡 想学 AI 应用开发？有了 `openai` 库，你可以立刻开始调用大语言模型。

### 🔬 网络与数据

| 库名 | 版本 | 用途 |
|------|------|------|
| requests | 2.32 | 网络请求（爬虫、调用 API） |
| validators | 0.35 | 数据验证（邮箱、网址格式检查） |

### 🔐 加密与安全

| 库名 | 版本 | 用途 |
|------|------|------|
| PyNaCl | 1.6 | 非对称加密、数字签名（ED25519 算法） |
| base58 | 2.1 | Base58 编解码，常用于地址生成 |
| mnemonic | 0.21 | BIP39 助记词生成，密钥管理 |
| rlp | 4.1 | RLP 编码，数据序列化 |
| eth-utils | 5.3 | 以太坊工具库 |
| aeknow | 7.0.0 | Aeternity 生态 SDK，支持智能合约开发 |

> 💡 这些库可用于学习现代密码学、身份认证、数据完整性验证等安全相关技术。
>
> 🔐 PyStart 内置的[去中心化用户系统](USER_SYSTEM.md)就是基于这些库实现的，可边用边学。

### 🛠️ 开发工具

| 库名 | 版本 | 用途 |
|------|------|------|
| pylint | 4.0 | 代码质量检查 |
| jedi | 0.19 | 代码补全引擎 |
| asttokens | 3.0 | 语法分析 |
| docutils | 0.22 | 文档工具 |

### 📦 其他实用库

| 库名 | 版本 | 用途 |
|------|------|------|
| pyserial | 3.5 | 串口通信（Arduino、单片机） |
| Send2Trash | 2.0 | 安全删除文件到回收站 |
| tqdm | 4.67 | 进度条显示 |
| colorama | 0.4 | 终端彩色输出 |

> 📝 **提示**：需要其他库？打开菜单「工具 → 管理包...」，搜索安装即可。无需命令行，小白也能轻松搞定。

---

## 🚀 探索版（Explorer）额外预装库

除了标准版的所有库，**探索版** 还预装了以下库，让你能探索更多领域：

### 📊 数据科学

| 库名 | 用途 |
|------|------|
| numpy | 数值计算基础，几乎所有数据分析教程都会用 |
| pandas | 数据分析利器，处理表格数据的“Excel 杀手” |
| matplotlib | 数据可视化，画图表必备 |

### 🖼️ 图像处理

| 库名 | 用途 |
|------|------|
| Pillow | 图片处理（裁剪、缩放、加水印） |
| qrcode | 二维码生成 |

### 📄 办公自动化

| 库名 | 用途 |
|------|------|
| openpyxl | Excel 文件读写 |
| python-docx | Word 文档操作 |

### 🌐 网页解析

| 库名 | 用途 |
|------|------|
| beautifulsoup4 | HTML 解析，爬虫入门必备 |
| lxml | 快速 XML/HTML 解析器 |

### 🎮 趣味编程

| 库名 | 用途 |
|------|------|
| pygame-ce | 2D 游戏开发（社区增强版） |

> 💡 探索版适合想要一步到位、尝试多个方向的学习者。体积稍大，但功能更丰富。

---

## AI 助手配置

PyStart 内置 AI 编程助手，可以帮你：
- 解释看不懂的代码
- 找出程序的 bug
- 回答编程问题

### 配置步骤

1. 打开菜单：**工具 → 配置AI API...**
2. 填写以下信息：

| 字段 | 说明 |
|------|------|
| API Key | 从服务商获取的密钥 |
| Base URL | API 地址 |
| Model | 模型名称 |

### 推荐服务商

| 服务商 | Base URL | 推荐模型 | 备注 |
|--------|----------|----------|------|
| **美团LongCat** | `https://api.longcat.chat/openai` | LongCat-Flash-Chat | 免费试用 |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | qwen-plus | 阿里云 |
| OpenAI | `https://api.openai.com/v1` | gpt-4o | 需要科学上网 |

> 💡 **新手建议**：截至2026年1月，LongCat（https://longcat.chat/） 注册即送免费token，非常适合学习使用。

### 使用方法

1. 在编辑器中选中一段代码
2. 右键 → 「AI：解释代码」
3. 或直接打开 Chat 面板对话

---

## 常见问题

### Q: 双击 PyStart.bat 闪退怎么办？

**A:** 检查解压路径是否包含中文或特殊字符。建议放在类似 `D:\PyStart` 的简单路径。

### Q: 怎么更新已安装的库？

**A:** 菜单「工具 → 管理包...」，选中要更新的包，点击升级按钮。

### Q: 程序运行后窗口一闪而过？

**A:** 在程序最后加一行：
```python
input("按回车键退出...")
```

### Q: 中文乱码怎么办？

**A:** 确保文件保存为 UTF-8 编码。PyStart 默认就是 UTF-8，一般不会有问题。

### Q: 可以用 PyStart 做项目吗？

**A:** 可以用于学习和小型项目。如果是大型生产项目，建议迁移到 VS Code 等开发平台。

---

## 系统要求

- **操作系统**：Windows 10 / 11
- **Python**：绿色版自带，pip 版需要 3.9+
- **硬盘空间**：约 200MB

---

## 致谢

PyStart 站在巨人的肩膀上：

- [Thonny](https://thonny.org) - Aivar Annamaa（爱沙尼亚塔尔图大学）
- [Python](https://python.org) - Python 软件基金会

---

## 许可证

MIT License

本项目基于 [Thonny](https://github.com/thonny/thonny) 二次开发。

---

## 联系我们

- 📦 PyPI: [pypi.org/project/pystart](https://pypi.org/project/pystart/)
- 🏠 GitHub: [github.com/AEKnow/PyStart](https://github.com/AEKnow/PyStart)
- 🐛 问题反馈: [Issues](https://github.com/AEKnow/PyStart/issues)
- ✉️ 邮箱: outcrop@gmail.com

---

<p align="center">
  <strong>Happy Coding! 🐍</strong><br>
  <sub>每个程序员都是从 print("Hello World") 开始的</sub>
</p>
