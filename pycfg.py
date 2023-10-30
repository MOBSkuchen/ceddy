import appstate as _state
from global_logging import log


CONFIG_FILE_NAME = "config.py"


class Absolute:
    """
    Absolute number of "pixels"
    """
    def __init__(self, val):
        self.val = val

    def getval(self):
        return self.val


class Percent:
    """
    Percent of the total possible screen size
    """
    def __init__(self, val):
        self.val = val

    def getval(self, per: float):
        return per / self.val


def _set_cfg_val(name, val):
    _state.add_item("cfg", name, val)


def run_py_cfg(import_name):
    ret_code = None  # To avoid intellisens errors
    exec_code = f"""
from {import_name} import main
ret_code = main(_state)
"""
    exec(exec_code)
    if ret_code is not None:
        log("PYCFG finished with return code:", ret_code)
    else:
        log("PYCFG finished without a return code")


def set_mode(mode: str):
    """
    Set the current input mode
    :param mode:
    Should be one of:
    "A" (append) / "O" (overwrite)
    """
    _state.add_item("var", "mode", mode)


def win_dim(name: str, x: Absolute | Percent, y: Absolute | Percent, width: Absolute | Percent,
            height: Absolute | Percent):
    """
    Set window dimensions
    :param name:
    Should be one of:
    - "gmi" General input window
    - "ent" Command entry window
    - "header" Info display window
    :param x:
    X position of the window,
    must be `Absolute` / `Percent` (of possible value)
    :param y:
    Y position of the window,
    must be `Absolute` / `Percent` (of possible value)
    :param width:
    Width of the window,
    must be `Absolute` / `Percent` (of possible value)
    :param height:
    Height of the window,
    must be `Absolute` / `Percent` (of possible value)

    For size measurements (height & width),
    a value of a -1 (remaining space) is possible.
    """
    _set_cfg_val(name, (x, y, width, height))


def shortcut(ch: int, trigger, lvl: str):
    """
    Set trigger-able shortcut for a character on a level
    :param ch:
    An integer character as returned by `getch`
    :param trigger:
    A function which handles the event:
    ``function(self, ch) -> bool``

    Takes in the following arguments:
    - self : The window class
    - ch : The character
    Returns:
    Whether the input handling should be stopped
    :param lvl:
    The level / which input is handled
    Must be one of the following:
    - "std" : Handles all input (but has least priority)
    - "gmi" : General input window
    - "ent" : Command entry window
    """
    _set_cfg_val(f'{lvl}_ksc_{ch}', trigger)
