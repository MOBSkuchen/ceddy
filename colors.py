import curses
import appstate as _state


COL_COUNT = 0


def init():
    _state.add_global_state("col")
