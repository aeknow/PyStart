# -*- coding: utf-8 -*-

"""Code for maintaining the background process and for running
user programs

Commands get executed via shell, this way the command line in the 
shell becomes kind of title for the execution.

""" 


from _thread import start_new_thread
import collections
from logging import debug
import os.path
import subprocess
import sys
import threading

from thonny.common import serialize_message, ToplevelCommand, \
    InlineCommand, parse_shell_command, \
    CommandSyntaxError, parse_message, DebuggerCommand, InputSubmission,\
    UserError
from thonny.globals import get_workbench, get_runner
from thonny.shell import ShellView
import shlex
from thonny import THONNY_USER_DIR
from thonny.misc_utils import running_on_windows, running_on_mac_os, eqfn,\
    delete_dir_try_hard
from shutil import which
import shutil
import time
import logging
import test

DEFAULT_CPYTHON_INTERPRETER = "default"

class Runner:
    def __init__(self):
        get_workbench().add_option("run.working_directory", os.path.expanduser("~"))
        get_workbench().add_option("run.auto_cd", True)
        get_workbench().add_option("run.backend_configuration", "Python (%s)" % DEFAULT_CPYTHON_INTERPRETER)
        get_workbench().add_option("run.used_interpreters", [])
        get_workbench().add_backend("Python", CPythonProxy)
        
        get_workbench().add_view(ShellView, "Shell", "s",
            visible_by_default=True,
            default_position_key='A')
        
        self._init_commands()
        
        self._proxy = None
        self.reset_backend()
        self._poll_vm_messages()
        self._advance_background_tk_mainloop()
    
    def _init_commands(self):
        shell = get_workbench().get_view("ShellView")
        shell.add_command("Run", self.handle_execute_from_shell)
        shell.add_command("Reset", self._handle_reset_from_shell)
        shell.add_command("cd", self._handle_cd_from_shell)
        
        get_workbench().add_command('run_current_script', "run", 'Run current script',
            handler=self._cmd_run_current_script,
            default_sequence="<F5>",
            tester=self.cmd_execution_command_enabled,
            group=10,
            image_filename="run.run_current_script.gif",
            include_in_toolbar=True)
        
        get_workbench().add_command('reset', "run", 'Stop/Reset',
            handler=self.cmd_stop_reset,
            default_sequence="<Control-F2>",
            tester=self._cmd_stop_reset_enabled,
            group=70,
            image_filename="run.stop.gif",
            include_in_toolbar=True)
    
    def get_cwd(self):
        # TODO: make it nicer
        if hasattr(self._proxy, "cwd"):
            return self._proxy.cwd
        else:
            return ""
    
    def get_state(self):
        """State is one of "running", "waiting_input", "waiting_debug_command",
            "waiting_toplevel_command"
        """
        return self._proxy.get_state()
    
    def get_sys_path(self):
        return self._proxy.get_sys_path()
    
    def send_command(self, cmd):
        self._proxy.send_command(cmd)
    
    def send_program_input(self, data):
        self._proxy.send_program_input(data)
        
    def execute_script(self, script_path, args, working_directory=None, command_name="Run"):
        if (working_directory is not None and self._proxy.cwd != working_directory):
            # create compound command
            # start with %cd
            cmd_line = "%cd " + shlex.quote(working_directory) + "\n"
            next_cwd = working_directory
        else:
            # create simple command
            cmd_line = ""
            next_cwd = self._proxy.cwd
        
        # append main command (Run, run, Debug or debug)
        rel_filename = os.path.relpath(script_path, next_cwd)
        cmd_line += "%" + command_name + " " + shlex.quote(rel_filename)
        
        # append args
        for arg in args:
            cmd_line += " " + shlex.quote(arg) 
        
        cmd_line += "\n"
        
        # submit to shell (shell will execute it)
        get_workbench().get_view("ShellView").submit_command(cmd_line)
        
    def execute_current(self, command_name, always_change_to_script_dir=False):
        """
        This method's job is to create a command for running/debugging
        current file/script and submit it to shell
        """
        
        editor = get_workbench().get_current_editor()
        if not editor:
            return

        filename = editor.get_filename(True)
        if not filename:
            return
        
        # changing dir may be required
        script_dir = os.path.realpath(os.path.dirname(filename))
        
        if (get_workbench().get_option("run.auto_cd") 
            and command_name[0].isupper() or always_change_to_script_dir):
            working_directory = script_dir
        else:
            working_directory = None
        
        self.execute_script(filename, [], working_directory, command_name)
        
    def handle_execute_from_shell(self, cmd_line):
        """
        Handles all commands that take a filename and 0 or more extra arguments.
        Passes the command to backend.
        
        (Debugger plugin may also use this method)
        """
        command, args = parse_shell_command(cmd_line)
        
        if len(args) >= 1:
            get_workbench().get_editor_notebook().save_all_named_editors()
            self.send_command(ToplevelCommand(command=command,
                               filename=args[0],
                               args=args[1:]))
        else:
            raise CommandSyntaxError("Command '%s' takes at least one argument", command)

    def _handle_reset_from_shell(self, cmd_line):
        command, args = parse_shell_command(cmd_line)
        assert command == "Reset"
        
        if len(args) == 0:
            self.send_command(ToplevelCommand(command="Reset"))
        else:
            raise CommandSyntaxError("Command 'Reset' doesn't take arguments")
        

    def _handle_cd_from_shell(self, cmd_line):
        command, args = parse_shell_command(cmd_line)
        assert command == "cd"
        
        if len(args) == 1:
            self.send_command(ToplevelCommand(command="cd", path=args[0]))
        else:
            raise CommandSyntaxError("Command 'cd' takes one argument")

    def cmd_execution_command_enabled(self):
        return (self._proxy.get_state() == "waiting_toplevel_command"
                and get_workbench().get_editor_notebook().get_current_editor() is not None)
    
    def _cmd_run_current_script(self):
        self.execute_current("Run")
    
    
    def cmd_stop_reset(self):
        if get_runner().get_state() == "waiting_toplevel_command":
            get_workbench().get_view("ShellView").submit_command("%Reset\n")
        else:
            get_runner().send_command(ToplevelCommand(command="Reset"))
    
            
    def _cmd_stop_reset_enabled(self):
        return True
            
    def _advance_background_tk_mainloop(self):
        """Enables running Tkinter programs which doesn't call mainloop. 
        
        When mainloop is omitted, then program can be interacted with
        from the shell after it runs to the end.
        """
        if self._proxy.get_state() == "waiting_toplevel_command":
            self._proxy.send_command(InlineCommand("tkupdate"))
        get_workbench().after(50, self._advance_background_tk_mainloop)
        
    def _poll_vm_messages(self):
        """I chose polling instead of event_generate in listener thread,
        because event_generate across threads is not reliable
        http://www.thecodingforums.com/threads/more-on-tk-event_generate-and-threads.359615/
        """
        while True:
            msg = self._proxy.fetch_next_message()
            if not msg:
                break
            
            debug("Runner: State: %s, Fetched msg: %s", self.get_state(), msg)
            get_workbench().event_generate(msg["message_type"], **msg)
            
            
            # TODO: maybe distinguish between workbench cwd and backend cwd ??
            get_workbench().set_option("run.working_directory", self.get_cwd())
            get_workbench().update()
            
        get_workbench().after(50, self._poll_vm_messages)
    
    def reset_backend(self):
        self.kill_backend()
        configuration = get_workbench().get_option("run.backend_configuration")
        backend_name, configuration_option = parse_configuration(configuration)
        backend_class = get_workbench().get_backends()[backend_name]
        self._proxy = backend_class(configuration_option)
        self.send_command(ToplevelCommand(command="Reset"))
        
    def kill_backend(self):
        if self._proxy:
            self._proxy.kill_current_process()
            self._proxy = None

    def get_interpreter_command(self):
        return self._proxy.get_interpreter_command()
    
    def get_backend_description(self):
        return self._proxy.get_description()

class BackendProxy:
    """Communicates with backend process.
    
    All communication methods must be non-blocking, 
    ie. suitable for calling from GUI thread."""
    
    def __init__(self, configuration_option):
        """If configuration is "Foo (bar)", then "Foo" is backend descriptor
        and "bar" is configuration option"""
    
    @classmethod
    def get_configuration_options(cls):
        """Returns a list strings for populating interpreter selection dialog.
        The strings are without backend descriptor"""
        raise NotImplementedError()
    
    def get_description(self):
        """Returns a string that describes the backend"""
        raise NotImplementedError()        

    def fetch_next_message(self):
        """Read next message from the queue or None if queue is empty"""
        raise NotImplementedError()

    def send_command(self, cmd):
        """Send the command to backend"""
        raise NotImplementedError()

    def send_program_input(self, data):
        """Send input data to backend"""
        raise NotImplementedError()
    
    def get_sys_path(self):
        "backend's sys.path"
        return []
    
    def get_state(self):
        """Get current state of backend.
        
        One of "running", "waiting_input", "waiting_toplevel_command", "waiting_debug_command" """
        raise NotImplementedError()

    def kill_current_process(self):
        "Kill the backend"
        raise NotImplementedError()
    
    def get_interpreter_command(self):
        """Return system command for invoking current interpreter"""
        raise NotImplementedError()
    

class CPythonProxy(BackendProxy):
    @classmethod
    def get_configuration_options(cls):
        return [DEFAULT_CPYTHON_INTERPRETER] + CPythonProxy._get_interpreters()
        
        
    def __init__(self, configuration_option):
        if configuration_option == DEFAULT_CPYTHON_INTERPRETER:
            self._executable = _get_private_venv_executable()
        else:
            self._executable = configuration_option
        
        cwd = get_workbench().get_option("run.working_directory")
        if os.path.exists(cwd):
            self.cwd = cwd
        else:
            self.cwd = os.path.expanduser("~")
            
        self._proc = None
        self._state = None
        self._message_queue = None
        self._state_lock = threading.RLock()
        self._sys_path = []
    
    def fetch_next_message(self):
        msg = self._fetch_next_message()
        
        if msg is not None:
            if msg["message_type"] == "ToplevelResult":
                self._set_state("waiting_toplevel_command") 
            elif msg["message_type"] == "DebuggerProgress":
                self._set_state("waiting_debug_command") 
            elif msg["message_type"] == "InputRequest":
                self._set_state("waiting_input")
        
        return msg 

    
    def _fetch_next_message(self):
        if not self._message_queue or len(self._message_queue) == 0:
            return None
        
        msg = self._message_queue.popleft()
        
        if msg["message_type"] == "ProgramOutput":
            # combine available output messages to one single message, 
            # in order to put less pressure on UI code
            
            while True:
                if len(self._message_queue) == 0:
                    return msg
                else:
                    next_msg = self._message_queue.popleft()
                    if (next_msg["message_type"] == "ProgramOutput" 
                        and next_msg["stream_name"] == msg["stream_name"]):
                        msg["data"] += next_msg["data"]
                    else:
                        # not same type of message, put it back
                        self._message_queue.appendleft(next_msg)
                        return msg
            
        else: 
            return msg
    
    def get_description(self):
        # TODO: show backend version and interpreter path
        return "Python (current dir: {})".format(self.cwd)
        
        
    def send_command(self, cmd):
        if not (isinstance(cmd, InlineCommand) and cmd.command == "tkupdate"): 
            debug("Proxy: Sending command: %s", cmd)
            
        with self._state_lock:
            if (isinstance(cmd, ToplevelCommand) 
                or isinstance(cmd, DebuggerCommand)
                or isinstance(cmd, InputSubmission)):
                self._set_state("running")
            
            if isinstance(cmd, ToplevelCommand) and cmd.command in ("Run", "Debug", "Reset"):
                self.kill_current_process()
                self._start_new_process(cmd)
                 
            self._proc.stdin.write(serialize_message(cmd) + "\n")
            self._proc.stdin.flush() 
            
            if not (hasattr(cmd, "command") and cmd.command == "tkupdate"):
                debug("BackendProxy: sent a command in state %s: %s", self._state, cmd)
    
    def send_program_input(self, data):
        self.send_command(InputSubmission(data=data))
        
    def get_state(self):
        with self._state_lock:
            return self._state
    
    def get_sys_path(self):
        return self._sys_path
    
    def _set_state(self, state):
        if self._state != state:
            debug("BackendProxy state changed: %s ==> %s", self._state, state)
            self._state = state
    
    
    def kill_current_process(self):
        if self._proc is not None and self._proc.poll() is None: 
            self._proc.kill()
            self._proc = None
            self._message_queue = None
    
    def _prepare_launcher(self):
        """Make jedi and required Thonny files available for the backend.
        
        I could prepare a special directory for this under thonny package (in thonny distribution), but
            - some files are required both by frontend and backend
            - jedi is required by the backend and I don't want to include it in thonny package
            - I don't want to duplicate files in distribution 
            - I don't want the distribution to require any preprocessing before running 
        
        For these reasons I decided that files required by the backend will be copied from 
        main original locations to a directory under THONNY_USER_DIR
        *after* installation, at runtime. As an optimization I won't re-copy if correct version
        is already in correct location. 
        """
        
        launch_dir = os.path.join(THONNY_USER_DIR, "backend")
        LAUNCHER_NAME = "backend_launcher.py"
        launcher_path = os.path.join(launch_dir, LAUNCHER_NAME)
        ver_file = os.path.join(launch_dir, "thonny", "VERSION")
        
        # if thonny VERSION file exists and is same as current version,
        # then we're done
        if os.path.exists(ver_file):
            with open(ver_file) as f:
                if f.read().strip() == get_workbench().get_version_str():
                    return launcher_path
        
        # Required stuff is not copied or is not meant for this Thonny version.
        logging.info("(re)creating backend launch dir")
        # First delete old version (if it exists)
        # start with VERSION so that it's clear that dir is not complete even if whole deletion fails
        if os.path.exists(ver_file):
            os.remove(ver_file)
        
        delete_dir_try_hard(launch_dir)            
        
        # Prepare launch directory
        if not os.path.exists(launch_dir):
            os.mkdir(launch_dir, 0o755)
            #os.makedirs(launch_dir, 0o755)
        
        # Copy thonny stuff
        thonny_source_dir = get_workbench().get_package_dir()
        
        # launch file sits originally in thonny package 
        # but for backend it will be in right in launch directory
        shutil.copyfile(os.path.join(thonny_source_dir, LAUNCHER_NAME),
                        os.path.join(launch_dir, LAUNCHER_NAME))
        
        # Copy relevant parts of thonny package
        thonny_dest_dir = os.path.join(launch_dir, "thonny")
        os.mkdir(thonny_dest_dir, 0o755)
        for name in ["__init__.py", "backend.py", "ast_utils.py", "common.py", "VERSION"]:
            shutil.copyfile(os.path.join(thonny_source_dir, name),
                            os.path.join(thonny_dest_dir, name))
        
        # Copy jedi
        import jedi
        shutil.copytree(jedi.__path__[0], os.path.join(launch_dir, "jedi"))
            
        # done
        return launcher_path
    
    def _start_new_process(self, cmd):
        self._message_queue = collections.deque()
    
        # create new backend process
        my_env = {}
        for name in os.environ:
            if ("python" not in name.lower() # skip python vars, because we may use different Python version
                and name not in ["TK_LIBRARY", "TCL_LIBRARY"]): # They tend to point to frontend Python installation 
                my_env[name] = os.environ[name]
        
        # TODO: take care of SSL_CERT_FILE
        # Unset when we're in builtin python and target python is external
        # And set, wen we're in external and target is builtin (or it's venv)
                
        my_env["PYTHONIOENCODING"] = "ASCII" 
        my_env["PYTHONUNBUFFERED"] = "1" 
        
        if not os.path.exists(self._executable):
            raise UserError("Interpreter (%s) not found. Please recheck corresponding option!"
                            % self._executable)
        
        
        backend_launcher = self._prepare_launcher() 
        
        cmd_line = [
            self._executable, 
            '-u', # unbuffered IO (neccessary in Python 3.1)
            '-B', # don't write pyo/pyc files 
                  # (to avoid problems when using different Python versions without write permissions)
            backend_launcher
        ]
        

        if hasattr(cmd, "filename"):
            cmd_line.append(cmd.filename)
            if hasattr(cmd, "args"):
                cmd_line.extend(cmd.args)
        
        if hasattr(cmd, "environment"):
            my_env.update(cmd.environment)            
        
        debug("Starting the backend: %s %s", cmd_line, self.cwd)
        self._proc = subprocess.Popen (
            cmd_line,
            #bufsize=0,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            env=my_env,
            universal_newlines=True
        )
        
        ready_line = self._proc.stdout.readline()
        if ready_line == "": # There was some problem
            error_msg = self._proc.stderr.read()
            raise Exception("Error starting backend process: " + error_msg)
        
        ready_msg = parse_message(ready_line)
        self._sys_path = ready_msg["path"]
        debug("Backend ready: %s", ready_msg, self._sys_path)
        get_workbench().event_generate("BackendReady", **ready_msg)
        
        # setup asynchronous output listeners
        start_new_thread(self._listen_stdout, ())
        start_new_thread(self._listen_stderr, ())
    
    def _listen_stdout(self):
        #debug("... started listening to stdout")
        # will be called from separate thread
        while True:
            data = self._proc.stdout.readline()
            #debug("... read some stdout data", repr(data))
            if data == '':
                break
            else:
                msg = parse_message(data)
                if "cwd" in msg:
                    self.cwd = msg["cwd"]
                    
                with self._state_lock:
                    self._message_queue.append(msg)

    def _listen_stderr(self):
        # stderr is used only for debugger debugging
        while True:
            data = self._proc.stderr.readline()
            if data == '':
                break
            else:
                debug("### BACKEND ###: %s", data.strip())
        


    @classmethod
    def _get_interpreters(cls):
        result = set()
        
        if running_on_windows():
            # registry
            result.update(CPythonProxy._get_interpreters_from_windows_registry())
            
            # Common locations
            for dir_ in ["C:\\Python34",
                         "C:\\Python35",
                         "C:\\Program Files\\Python 3.5",
                         "C:\\Program Files (x86)\\Python 3.5",
                         "C:\\Python36",
                         "C:\\Program Files\\Python 3.6",
                         "C:\\Program Files (x86)\\Python 3.6",
                         ]:
                path = os.path.join(dir_, "pythonw.exe")
                if os.path.exists(path):
                    result.add(os.path.realpath(path))  
        
        else:
            # Common unix locations
            for dir_ in ["/bin", "/usr/bin", "/usr/local/bin",
                         os.path.expanduser("~/.local/bin")]:
                for name in ["python3", "python3.4", "python3.5", "python3.6"]:
                    path = os.path.join(dir_, name)
                    if os.path.exists(path):
                        result.add(path)  
        
        if running_on_mac_os():
            for version in ["3.4", "3.5", "3.6"]:
                dir_ = os.path.join("/Library/Frameworks/Python.framework/Versions",
                                    version, "bin")
                path = os.path.join(dir_, "python3")
                
                if os.path.exists(path):
                    result.add(path)
        
        for command in ["pythonw", "python3", "python3.4", "python3.5", "python3.6"]:
            path = which(command)
            if path is not None:
                result.add(path)
        
        current_configuration = get_workbench().get_option("run.backend_configuration")
        backend, configuration_option = parse_configuration(current_configuration)
        if backend == "Python" and configuration_option and os.path.exists(configuration_option):
            result.add(os.path.realpath(configuration_option))
        
        for path in get_workbench().get_option("run.used_interpreters"):
            if os.path.exists(path):
                result.add(os.path.realpath(path))
        
        return sorted(result)
    
    
    @classmethod
    def _get_interpreters_from_windows_registry(cls):
        import winreg
        result = set()
        for key in [winreg.HKEY_LOCAL_MACHINE,
                    winreg.HKEY_CURRENT_USER]:
            for version in ["3.4",
                            "3.5", "3.5-32", "3.5-64",
                            "3.6", "3.6-32", "3.6-64"]:
                try:
                    for subkey in [
                        'SOFTWARE\\Python\\PythonCore\\' + version + '\\InstallPath',
                        'SOFTWARE\\Python\\PythonCore\\Wow6432Node\\' + version + '\\InstallPath'
                                 ]:
                        dir_ = winreg.QueryValue(key, subkey)
                        if dir_:
                            path = os.path.join(dir_, "pythonw.exe")
                            if os.path.exists(path):
                                result.add(path)
                except:
                    pass
        
        return result
    
    def _get_gui_interpreter(self):
        if sys.executable.endswith("thonny.exe"):
            # assuming that thonny.exe is in the same dir as pythonw.exe
            # (NB! thonny.exe in scripts folder delegates running to python.exe)
            return sys.executable.replace("thonny.exe", "pythonw.exe")
        else:
            return sys.executable
    
    def get_interpreter_command(self):
        return self._executable

def parse_configuration(configuration):
    """
    "Python (C:\Python34\pythonw.exe)" becomes ("Python", "C:\Python34\pythonw.exe")
    "BBC micro:bit" becomes ("BBC micro:bit", "")
    """
    
    parts = configuration.split("(", maxsplit=1)
    if len(parts) == 1:
        return configuration, ""
    else:
        return parts[0].strip(), parts[1].strip(" )")


def prepare_private_venv():
    path = _get_private_venv_path()
    if os.path.isdir(path):
        _check_upgrade_private_venv(path)
    else:
        _create_private_venv(path, "Please wait!\nThonny prepares its virtual environment .")

def _check_upgrade_private_venv(path):
    # If home is wrong then regenerate
    # If only micro version is different, then upgrade
    info = _get_venv_info(path)
    
    if not eqfn(info["home"], os.path.dirname(sys.executable)):
        _create_private_venv(path, 
                             "Thonny's virtual environment was created for another interpreter.\n"
                             + "Regenerating the virtual environment for current interpreter.\n"
                             + "(You may need to reinstall your 3rd party packages)\n"
                             + "Please wait! .",
                             clear=True)
    else:
        venv_version = tuple(map(int, info["version"].split(".")))
        sys_version = sys.version_info[:3]
        assert venv_version[0] == sys_version[0]
        assert venv_version[1] == sys_version[1]
        
        if venv_version[2] != sys_version[2]:
            _create_private_venv(path, "Please wait!\nUpgrading Thonny's virtual environment .",
                                 upgrade=True)
            

def _create_private_venv(path, description, clear=False, upgrade=False):
    base_exe = sys.executable
    if sys.executable.endswith("thonny.exe"):
        # assuming that thonny.exe is in the same dir as pythonw.exe
        # (NB! thonny.exe in scripts folder delegates running to python.exe)
        base_exe = sys.executable.replace("thonny.exe", "pythonw.exe")
    
    
    def action():
        
        # Don't include system site packages
        # This way all students will have similar configuration
        # independently of system Python (if Thonny is used with system Python)
        
        # NB! Cant run venv.create directly, because in Windows 
        # it tries to link venv to thonny.exe.
        # Need to run it via proper python
        cmd = [base_exe, "-m", "venv"]
        if clear:
            cmd.append("--clear")
        if upgrade:
            cmd.append("--upgrade")
            
        cmd.append(path)
        p = subprocess.Popen(cmd)
        p.wait()
         
    from thonny.ui_utils import run_with_busy_window
    run_with_busy_window(action, description=description)
    
    bindir = os.path.dirname(_get_private_venv_executable())
    # create private env marker
    marker_path = os.path.join(bindir, "is_private")
    with open(marker_path, mode="w") as fp:
        fp.write("# This file marks Thonny-private venv")
    
    # Create recommended pip conf to get rid of list deprecation warning
    # https://github.com/pypa/pip/issues/4058
    pip_conf = "pip.ini" if running_on_windows() else "pip.conf"
    with open(os.path.join(path, pip_conf), mode="w") as fp:
        fp.write("[list]\nformat = columns")
    
    assert os.path.isdir(path)
    
    
def _get_private_venv_path():
    if "thonny" in sys.executable.lower():
        prefix = "BundledPython"
    else:
        prefix = "Python" 
    return os.path.join(THONNY_USER_DIR, prefix + "%d%d" % (sys.version_info[0], sys.version_info[1]))

def _get_private_venv_executable():
    venv_path = _get_private_venv_path()
    assert os.path.exists(venv_path)
    
    if running_on_windows():
        exe = os.path.join(venv_path, "Scripts", "pythonw.exe")
    else:
        exe = os.path.join(venv_path, "bin", "python3")
    
    assert os.path.exists(exe)
    return exe

def _get_venv_info(venv_path):
    cfg_path = os.path.join(venv_path, "pyvenv.cfg")
    result = {}
    
    with open(cfg_path, encoding="UTF-8") as fp:
        for line in fp:
            if "=" in line:
                key, val = line.split("=", maxsplit=1)
                result[key.strip()] = val.strip()
    
    return result;
    