# -*- coding: utf-8 -*-
"""Adds commands for opening certain PyStart folders"""

from pystart import get_pystart_user_dir, get_workbench
from pystart.languages import tr
from pystart.ui_utils import open_path_in_system_file_manager


def load_plugin() -> None:
    def cmd_open_data_dir():
        open_path_in_system_file_manager(get_pystart_user_dir())

    def cmd_open_program_dir():
        open_path_in_system_file_manager(get_workbench().get_package_dir())

    get_workbench().add_command(
        "open_program_dir",
        "tools",
        tr("Open PyStart program folder..."),
        cmd_open_program_dir,
        group=110,
    )
    get_workbench().add_command(
        "open_data_dir", "tools", tr("Open PyStart data folder..."), cmd_open_data_dir, group=110
    )
