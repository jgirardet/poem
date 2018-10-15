import re
import sublime
from .consts import (
    PACKAGE_NAME,
)

import pathlib
import subprocess
import signal
import os
from functools import partial
import socket
import requests
import logging
import yaml

LOG = logging.getLogger(PACKAGE_NAME)


class Path(type(pathlib.Path())):
    def write_text(
        self, content, mode="w", buffering=-1, encoding=None, errors=None, newline=None
    ):

        with self.open(
            mode="w", buffering=-1, encoding=None, errors=None, newline=None
        ) as file:

            return file.write(content)

    def read_text(
        self, mode="w", buffering=-1, encoding=None, errors=None, newline=None
    ):

        with self.open(
            mode="r", buffering=-1, encoding=None, errors=None, newline=None
        ) as file:

            return file.read()


def timed(fn):
    def to_time(*args, **kwargs):
        import time

        st = time.time()
        rev = fn(*args, **kwargs)
        end = time.time()
        LOG.debug("durée {} {:.2f} ms".format(fn.__name__, (end - st) * 1000))
        return rev

    return to_time




def get_settings(view):
    flat_settings = view.settings()
    nested_settings = flat_settings.get(PACKAGE_NAME, {})
    global_settings = sublime.load_settings(SETTINGS_FILE_NAME)
    pyproject_settings = read_pyproject_toml(find_root_file(view, "pyproject.toml"))
    settings = {}

    for k in CONFIG_OPTIONS:
        # 1. pyproject
        value = pyproject_settings.get(k[6:].replace("_", "-"), None)
        if value:
            settings[k] = value
            continue

        # 2. check sublime "flat settings"
        value = flat_settings.get(SETTINGS_NS_PREFIX + k, KEY_ERROR_MARKER)
        if value != KEY_ERROR_MARKER:
            settings[k] = value
            continue

        # 3. check sublieme "nested settings" for compatibility reason
        value = nested_settings.get(k, KEY_ERROR_MARKER)
        if value != KEY_ERROR_MARKER:
            settings[k] = value
            continue

        # 4. check plugin/user settings
        settings[k] = global_settings.get(k)

    return settings


def startup_info():
    "running windows process in background"
    if sublime.platform() == "windows":
        st = subprocess.STARTUPINFO()
        st.dwFlags = (
            subprocess.STARTF_USESHOWWINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        st.wShowWindow = subprocess.SW_HIDE
        return st
    else:
        return None


def kill_with_pid(pid: int):
    if sublime.platform() == "windows":
        # need to properly kill precess traa
        subprocess.call(
            ["taskkill", "/F", "/T", "/PID", str(pid)], startupinfo=startup_info()
        )
    else:
        os.kill(pid, signal.SIGTERM)


popen = partial(subprocess.Popen, startupinfo=startup_info())



def find_root_file(view, filename):
    """Only search in projects and folders since pyproject.toml/precommit, ... should be nowhere else"""
    window = view.window()
    variables = window.extract_variables()
    # project path
    path = Path(variables.get("project_path", "")) / filename
    if path.exists():
        LOG.debug("%s path %s", filename, path)
        return path

    # folders
    folders = window.folders()

    for path in folders:
        LOG.debug("Folders : %s", path)
        path = Path(path) / filename
        if path.exists():

            LOG.debug("%s path %s", filename, path)
            return path

    # nothing found
    return None


############################
# Let it like this wainting for toml depedency in package contrl
# https://github.com/wbond/package_control_channel/pull/7298
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import toml

###################""


def read_pyproject_toml(pyproject: Path) -> dict:
    """Return config options foud in pyproject"""
    config = {}
    if not pyproject:
        LOG.debug("No pyproject.toml file found")
        return {}

    try:
        pyproject_toml = toml.load(str(pyproject))
        config = pyproject_toml.get("tool", {}).get("black", {})
    except (toml.TomlDecodeError, OSError) as e:
        LOG.error("Error reading configuration file: %s", pyproject)
        # pass

    LOG.debug("config values extracted from %s : %r", pyproject, config)
    return config
