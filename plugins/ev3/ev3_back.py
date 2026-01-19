import os.path
import sys
from logging import getLogger
from typing import List, Optional

# make sure thonny folder is in sys.path (relevant in dev)
thonny_container = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if thonny_container not in sys.path:
    sys.path.insert(0, thonny_container)

import pystart
from pystart.common import PROCESS_ACK
from pystart.plugins.micropython.os_mp_backend import SshUnixMicroPythonBackend

logger = getLogger("pystart.plugins.ev3.ev3_back")


class EV3MicroPythonBackend(SshUnixMicroPythonBackend):
    pass


if __name__ == "__main__":
    pystart.configure_backend_logging()
    print(PROCESS_ACK)

    import ast

    args = ast.literal_eval(sys.argv[1])

    EV3MicroPythonBackend(args)
