import os.path

import appstate as state
from pycfg import CONFIG_FILE_NAME, run_py_cfg
import curses
from global_logging import log


def dict_merge(*args):
    _ = {}
    for i in args:
        for n, d in i.items():
            _[n] = d
    return _


# Standard entry keybinds
sENT_KEYBINDS = {
    "UP": curses.KEY_UP,
    "DOWN": curses.KEY_DOWN,
    "LEFT": curses.KEY_LEFT,
    "RIGHT": curses.KEY_RIGHT,

    "PPAGE": curses.KEY_PPAGE,
    "NPAGE": curses.KEY_NPAGE,

    "BACKSPACE": 8,
    "ENTER": 10,
    "ESCAPE": 27,
    "DELETE": 330
}

FTR_KEYBINDS = dict_merge({
    "SELECT": sENT_KEYBINDS["ENTER"],
    "NEWFILE": sENT_KEYBINDS["BACKSPACE"],
    "REMOVE": sENT_KEYBINDS["DELETE"]
}, sENT_KEYBINDS)

STD_KEYBINDS = {
    "STD": sENT_KEYBINDS,
    "FTR": FTR_KEYBINDS
}


def get_keybind_act(action, level="STD"):
    """
    Return the char / key number (:int) for this action
    :param action:
    The action in question
    :param level:
    The level (input processor) which handles this
    :return:
    The char (:int)
    """
    _ = state.get_item("kbf", f'AF-{level}_{action}')
    if _ is None and not level == "STD":
        return get_keybind_act(action, "STD")
    return _


def get_keybind_chr(ch, level="STD"):
    return state.get_item("kbf", f'CF-{level}_{ch}')


def apply_keybind_act(action, ch, level="STD"):
    state.add_item("kbf", f'AF-{level}_{action}', ch)


def apply_std_keybinds():
    state.add_global_state("kbf")

    for l, d in STD_KEYBINDS.items():
        for a, c in d.items():
            apply_keybind_act(a, c, l)


def init():
    if not os.path.exists(CONFIG_FILE_NAME):
        log("No loadable config found")
        log("Fall back to standard keybindings")
        apply_std_keybinds()
    else:
        load_config()


def load_config():
    log("Trying to load config from standard config file:", CONFIG_FILE_NAME)
    import_name = CONFIG_FILE_NAME[:-3]
    run_py_cfg(import_name)


init()
