from pystart import get_workbench, is_portable
from pystart.languages import tr
from pystart.plugins.cpython_frontend.cp_front import (
    LocalCPythonConfigurationPage,
    LocalCPythonProxy,
    get_default_cpython_executable_for_backend,
)
import os


def load_plugin():
    wb = get_workbench()
    default_exe = get_default_cpython_executable_for_backend()
    
    wb.set_default("run.backend_name", "LocalCPython")
    wb.set_default("LocalCPython.last_executables", [])
    wb.set_default("LocalCPython.executable", default_exe)

    # For portable version, always use the bundled Python
    # This fixes the issue when copying to a different directory
    if is_portable():
        saved_exe = wb.get_option("LocalCPython.executable")
        # If saved path doesn't exist or is different from current bundled Python
        if not os.path.exists(saved_exe) or saved_exe != default_exe:
            wb.set_option("LocalCPython.executable", default_exe)

    if wb.get_option("run.backend_name") in ["PrivateVenv", "SameAsFrontend", "CustomCPython"]:
        # Removed in PyStart 4.0
        wb.set_option("run.backend_name", "LocalCPython")
        wb.set_option("LocalCPython.executable", default_exe)

    wb.add_backend(
        "LocalCPython",
        LocalCPythonProxy,
        tr("Local Python 3"),
        LocalCPythonConfigurationPage,
        "02",
    )
