# -*- coding: utf-8 -*-

import platform
import sys
import os
import webbrowser

import tkinter as tk
import tkinter.font
from logging import getLogger
from tkinter import ttk

import pystart
from pystart import get_workbench, ui_utils
from pystart.common import get_python_version_string
from pystart.languages import tr
from pystart.ui_utils import CommonDialogEx, create_url_label

logger = getLogger(__name__)


class AboutDialog(CommonDialogEx):
    def __init__(self, master):
        super().__init__(master)
        
        self.title(tr("关于 PyStart"))
        self.resizable(height=tk.FALSE, width=tk.FALSE)
        
        # 设置窗口宽度
        self.main_frame.configure(padding=25)
        
        self._create_header()
        self._create_info_section()
        self._create_links_section()
        self._create_footer()
        
        self.bind("<Return>", self.on_close, True)
        self.bind("<Escape>", self.on_close, True)
    
    def _create_header(self):
        """创建头部标题区域"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(sticky="ew", pady=(0, 15))
        
        # 大标题
        title_font = tkinter.font.nametofont("TkHeadingFont").copy()
        title_font.configure(size=20, weight="bold")
        
        title_label = ttk.Label(
            header_frame, 
            text="🚀 PyStart", 
            font=title_font
        )
        title_label.pack()
        
        # 版本号
        version_font = tkinter.font.nametofont("TkDefaultFont").copy()
        version_font.configure(size=11)
        
        version_label = ttk.Label(
            header_frame,
            text=f"v{pystart.get_version()}",
            font=version_font,
            foreground="#666666"
        )
        version_label.pack(pady=(2, 0))
        
        # 副标题
        slogan_font = tkinter.font.nametofont("TkDefaultFont").copy()
        slogan_font.configure(size=10)
        
        subtitle_label = ttk.Label(
            header_frame,
            text="零配置启动，让编程从第一行代码开始",
            font=slogan_font,
            foreground="#666666"
        )
        subtitle_label.pack(pady=(8, 0))
        
        # 微信二维码
        try:
            img_path = os.path.join(
                os.path.dirname(sys.modules["pystart"].__file__), 
                "res", "wechat.png"
            )
            self._wechat_image = tk.PhotoImage(file=img_path)
            
            img_label = tk.Label(header_frame, image=self._wechat_image)
            img_label.pack(pady=(10, 0))
            
            tip_label = ttk.Label(
                header_frame, 
                text="扫码加入 PyStart 用户群",
                foreground="#888888"
            )
            tip_label.pack(pady=(3, 0))
        except Exception:
            pass
    
    def _create_info_section(self):
        """创建信息区域"""
        info_frame = ttk.LabelFrame(self.main_frame, text="系统信息", padding=10)
        info_frame.grid(sticky="ew", pady=(0, 15))
        info_frame.columnconfigure(1, weight=1)
        
        # 系统信息
        info_items = [
            ("Python 版本", get_python_version_string()),
            ("操作系统", f"{platform.system()} {platform.release()}"),
            ("系统架构", platform.machine()),
        ]
        
        for i, (label, value) in enumerate(info_items):
            ttk.Label(info_frame, text=f"{label}：", foreground="#666666").grid(
                row=i, column=0, sticky="w", padx=(0, 10), pady=2
            )
            ttk.Label(info_frame, text=value).grid(
                row=i, column=1, sticky="w", pady=2
            )
    
    def _create_links_section(self):
        """创建链接区域"""
        links_frame = ttk.LabelFrame(self.main_frame, text="资源链接", padding=10)
        links_frame.grid(sticky="ew", pady=(0, 15))
        
        links = [
            ("🌐 官方网站", "https://pystart.org"),
            ("💻 开源仓库", "https://github.com/AEKnow/PyStart"),
            ("📖 Python 官方文档", "https://docs.python.org/zh-cn/3/"),
        ]
        
        for text, url in links:
            link_label = create_url_label(links_frame, url, text)
            link_label.pack(anchor="w", pady=2)
    
    def _create_footer(self):
        """创建底部区域"""
        footer_frame = ttk.Frame(self.main_frame)
        footer_frame.grid(sticky="ew")
        
        # 版权信息
        copyright_font = tkinter.font.nametofont("TkDefaultFont").copy()
        copyright_font.configure(size=9)
        
        copyright_text = (
            "PyStart 基于 Thonny 深度定制\n"
            "原作者: Aivar Annamaa @ University of Tartu\n"
            "MIT License | © 2024 - AEKnow"
        )
        
        copyright_label = ttk.Label(
            footer_frame,
            text=copyright_text,
            font=copyright_font,
            foreground="#999999",
            justify=tk.CENTER
        )
        copyright_label.pack(pady=(0, 15))
        
        # 关闭按钮
        btn_frame = ttk.Frame(footer_frame)
        btn_frame.pack()
        
        ok_button = ttk.Button(
            btn_frame, 
            text="关闭", 
            command=self.on_close, 
            default="active",
            width=12
        )
        ok_button.pack()
        ok_button.focus_set()


def load_plugin() -> None:
    def open_about():
        ui_utils.show_dialog(AboutDialog(get_workbench()))

    def open_url(url):
        import webbrowser

        # webbrowser.open returns bool, but add_command expects None
        webbrowser.open(url)

    get_workbench().add_command(
        "issues",
        "help",
        tr("反馈问题"),
        open_about,
        group=60,
    )
    get_workbench().add_command("about", "help", tr("关于PyStart"), open_about, group=61)

    # For Mac
    get_workbench().createcommand("tkAboutDialog", open_about)
