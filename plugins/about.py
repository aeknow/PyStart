# -*- coding: utf-8 -*-

import datetime
import platform
import sys
import os

import tkinter as tk
import tkinter.font
from logging import getLogger
from tkinter import ttk

import pystart
from pystart import get_workbench, ui_utils
from pystart.common import get_python_version_string
from pystart.languages import tr
from pystart.ui_utils import CommonDialog, CommonDialogEx, create_url_label, get_hyperlink_cursor

logger = getLogger(__name__)


class AboutDialog(CommonDialogEx):
    def __init__(self, master):
        super().__init__(master)

        self.title(tr("About PyStart"))
        self.resizable(height=tk.FALSE, width=tk.FALSE)

        default_heading_font = tkinter.font.nametofont("TkHeadingFont")
        heading_font = default_heading_font.copy()
        heading_font.configure(size=int(default_heading_font["size"] * 1.7), weight="bold")
        heading_label = ttk.Label(
            self.main_frame, text="PyStart " + pystart.get_version(), font=heading_font
        )
        heading_label.grid(pady=(self.get_large_padding(), self.get_small_padding()))

       

         # 读取图片文件        
        tk_image = tk.PhotoImage(file = os.path.dirname(sys.modules["pystart"].__file__)+'\\res\\wechat.png') 
        
        # 在窗口中显示图片  
        label_wechat = tk.Label(self.main_frame, image=tk_image)  
        label_wechat.image=tk_image#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!M<<<<================================非常重要
        label_wechat.grid()

        we_label = ttk.Label(
            self.main_frame,
            justify=tk.CENTER,
            text="加微信支持或访问网站：",
        )
        we_label.grid(pady=self.get_medium_padding())

        url_label = create_url_label(self.main_frame, "https://pystart.org\n", justify=tk.CENTER)
        url_label.grid()



        credits_label = create_url_label(
            self.main_frame,
            "https://github.com/pystart/thonny",
            tr(
                "PyStart is built from PyStart, by:\n"
                + "Aivar Annamaa\n@University of Tartu, Estonia,\n"
            ),
            justify=tk.CENTER,
        )
        credits_label.grid()

        default_font = tkinter.font.nametofont("TkDefaultFont")
        license_font = default_font.copy()
        license_font.configure(size=round(default_font["size"] * 0.7))
        license_label = ttk.Label(
            self.main_frame,
            text="Copyright (©) "           
            + tr(
                "This program comes with\n"
                + "ABSOLUTELY NO WARRANTY!\n"
                + "It is free software, and you are welcome to\n"
                + "redistribute it under certain conditions, see\n"
                + "https://opensource.org/licenses/MIT\n"
                + "for details"
            ),
            justify=tk.CENTER,
            font=license_font,
        )
        license_label.grid(pady=self.get_medium_padding())

        ok_button = ttk.Button(
            self.main_frame, text=tr("OK"), command=self.on_close, default="active"
        )
        ok_button.grid(pady=(0, self.get_large_padding()))
        ok_button.focus_set()

        self.bind("<Return>", self.on_close, True)

    def get_os_word_size_suffix(self):
        if "32" in platform.machine() and "64" not in platform.machine():
            return " (32-bit)"
        else:
            return ""


def load_plugin() -> None:
    def open_about():
        ui_utils.show_dialog(AboutDialog(get_workbench()))

    def open_url(url):
        import webbrowser

        # webbrowser.open returns bool, but add_command expects None
        webbrowser.open(url)

    get_workbench().add_command(
        "changelog",
        "help",
        tr("Version history"),
        lambda: open_url("https://github.com/pystart/thonny/blob/master/CHANGELOG.rst"),
        group=60,
    )
    get_workbench().add_command(
        "issues",
        "help",
        tr("Report problems"),
        lambda: open_url("https://github.com/pystart/thonny/issues"),
        group=60,
    )
    get_workbench().add_command("about", "help", tr("关于PyStart"), open_about, group=61)

    # For Mac
    get_workbench().createcommand("tkAboutDialog", open_about)
