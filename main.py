import curses
import curses.ascii
import os
import sys
import os_flags as flags
from window import Window, Textbox
import appstate as state


KEY_YES = 25
KEY_NO = 14
KEY_QUIT = 17

PROG = sys.argv.pop(0)

if len(sys.argv) > 0:
    CSF = sys.argv.pop(0)
else:
    CSF = None


def init():
    stdscr = curses.initscr()
    state.add_item("scr", "stdscr", stdscr)
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)

    return stdscr


def get_keybinds():
    state.add_global_state("kbs")

    dsp = flags.get_data_store_path("ceddy")
    if not os.path.exists(dsp):
        os.mkdir(dsp)
    if not os.path.exists(os.path.join(dsp, "keybinds.json")):
        pass


def cleanup_state_qa():
    state.add_item("var", "qas", False)
    state.add_item("var", "qaf", None)

    update_header()


def cleanup_ent_submit():
    state.add_item("var", "esf", None)
    update_header()


def change_file_name(text):
    global CSF
    CSF = text
    cleanup_ent_submit()


def change_mode(mode):
    state.add_item("var", "mode", mode)
    update_header()


def bas_input_processor(self: Textbox, ch):
    match ch:
        case 17:
            update_header("Exit?")
            state.add_item("var", "qas", True)
            state.add_item("var", "qaf", lambda ch_: True if ch_ == 25 else False)
        case 25:
            if not state.get_item("var", "qas"):
                return
            f = state.get_item("var", "qaf")
            cleanup_state_qa()
            return f(ch)
        case 14:
            if not state.get_item("var", "qas"): return
            f = state.get_item("var", "qaf")
            cleanup_state_qa()
            return f(ch)


def std_input_processor(self: Textbox, ch):
    match ch:
        case 15:
            change_mode("O")
        case 1:
            change_mode("A")
        case 19:
            if CSF is None:
                update_header("Please select a file")
            else:
                with open(CSF, 'w') as file:
                    file.write(state.get_item("scr", "gmi").text)
        case 434:
            update_header("Enter new filename")
            state.add_item("var", "esf", change_file_name)
            entry_focus()
        case 24:
            update_header("Select new file")

    return bas_input_processor(self, ch)


def textbox_focus():
    state.add_item("var", "ent", False)
    state.add_item("var", "gmi", True)
    tb = state.get_item("scr", "gmi")
    edit(tb)


def entry_focus():
    state.add_item("var", "gmi", False)
    state.add_item("var", "ent", True)
    entry = state.get_item("scr", "ent")
    edit(entry)


def ent_input_processor(self: Textbox, ch):
    match ch:
        case 5:
            textbox_focus()
        case 10:
            f = state.get_item("var", "esf")
            if f is not None:
                f(self.text)
            else:
                update_header("No action selected")

    return std_input_processor(self, ch)


def gmi_input_processor(self: Textbox, ch):
    match ch:
        case 5:
            entry_focus()
        case 421:
            self.deleteline()

    return std_input_processor(self, ch)


def update_header_r(text):
    header = state.get_item("scr", "header")
    if header is None: return
    header.win.erase()
    header.resize(len(text) + 1, 1)
    header.puttext(text)
    header.refresh()

    entry = state.get_item("scr", "ent")
    entry.win.erase()
    entry.reposition(len(text), 0)

    entry.refresh()
    header.refresh()


def update_header(note=None):
    mode = state.get_item("var", "mode")
    if CSF is not None:
        text = f"{CSF} [{mode}]"
    else:
        text = f"NONE [{mode}]"

    if note is not None:
        text += f' | {note}'

    text += " > "

    update_header_r(text)


def edit(win):
    win.focus()
    win.refresh()
    win.edit()


def main():
    stdscr = init()
    state.add_item("var", "mode", "O")
    import shortcuts
    header = Window(0, 0, 20, 1, "header")

    entry = Textbox(20, 0, -1, 1, "ent", input_processor=ent_input_processor)

    divider = Window(0, 1, curses.COLS, 1, "div")
    divider.win.hline(curses.ACS_HLINE, curses.COLS)
    divider.refresh()

    tb = Textbox(0, 2, -1, -1, "gmi", input_processor=gmi_input_processor)

    update_header()

    edit(tb)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
