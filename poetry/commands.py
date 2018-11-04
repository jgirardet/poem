from collections import defaultdict
import logging

import sublime_plugin
import sublime

from .poetry import Poetry
from .compat import VENV_BIN_DIR
from .utils import poetry_used, timed
from .consts import PACKAGE_NAME
from .command_runner import PoetryThread, ThreadProgress

LOG = logging.getLogger(PACKAGE_NAME)


class PoetryCommand(sublime_plugin.WindowCommand):
    def is_active(self):
        return poetry_used(self.window.active_view())

    is_enabled = is_active

    def run_command(self, command, *args):
        self.poetry = Poetry(self.window)
        runner = PoetryThread(command, self.poetry, *args)
        runner.start()
        ThreadProgress(runner)

    def run_input_command(self, caption, command, custom=""):
        if custom:
            self.run_command(command, custom)
        else:
            self.window.show_input_panel(
                caption, "", lambda x: self.run_command(command, x), None, None
            )


class PoetrySetPythonInterpreterCommand(PoetryCommand):
    def run(self):
        self.poetry = Poetry(self.window)
        project = defaultdict(dict)
        project.update(self.window.project_data())
        python_interpreter = self.poetry.venv / VENV_BIN_DIR / "python"

        project["settings"]["python_interpreter"] = str(python_interpreter)
        self.window.set_project_data(project)


class PoetryInstallCommand(PoetryCommand):
    def run(self):
        self.run_command("install")


class PoetryInstallNoDevCommand(PoetryCommand):
    def run(self):
        self.run_command("install --no-dev")


class PoetryUpdateCommand(PoetryCommand):
    def run(self):
        self.run_command("update")


class PoetryAddCommand(PoetryCommand):
    def run(self, custom=""):
        self.run_input_command("Poetry add", "add", custom)


class PoetryAddDevCommand(PoetryCommand):
    def run(self, custom=""):
        self.run_input_command("Poetry add", "add -D", custom)


# remove
# removedev
# update
