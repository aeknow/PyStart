from pystart import get_workbench
from pystart.languages import tr


def load_plugin():
    from pystart.plugins.uv.uv_front import LocalCPythonUvConfigurationPage, LocalCPythonUvProxy

    backend_name = "LocalCPythonUv"
    get_workbench().set_default(f"{backend_name}.python", "auto")

    get_workbench().add_backend(
        backend_name,
        LocalCPythonUvProxy,
        tr("Local Python 3") + " (uv)",
        LocalCPythonUvConfigurationPage,
        "03",
    )
