import msvcrt
import appstate as _state
import os
import curses
import shutil
from window import Window, Textbox
from curses import wrapper
from shortcuts import get_keybind_act
from main import bas_input_processor, update_header

DIR_DEPTH_MOD = 1
FILE_DEPTH_MOD = 2
RMT_ERR_C = 0
PENDING_REFRESH = True
PENDING_REMOVE_NAME: str = None
start = 'C:/Users/Jasper'
show_hidden = False


def pad(data, width):
    return data + ' ' * (width - len(data))


def list_dir_only(d):
    sds = []
    for sd in os.listdir(d):
        if os.path.isdir(os.path.join(d, sd)):
            if not show_hidden and sd not in ('.', '..') and sd[0] == '.':
                continue
            sds.append(sd)

    return sorted(sds)


def list_file_only(d):
    sds = []
    for sd in os.listdir(d):
        if os.path.isfile(os.path.join(d, sd)):
            if not show_hidden and sd not in ('.', '..') and sd[0] == '.':
                continue
            sds.append(sd)
    return sorted(sds)


class File(object):
    def __init__(self, name):
        self.name = name

    def render(self, depth, width):
        return pad('%s %s' % (' ' * FILE_DEPTH_MOD * depth,
                              os.path.basename(self.name)), width)

    def expand(self): pass

    def collapse(self): pass


class Dir(object):
    def __init__(self, name):
        # File.__init__(self, name)
        self.expanded = None
        self.kids = None
        self.kidnames2 = None
        self.kidnames = None
        self.name = name
        self.refresh()

    def refresh(self):
        try:
            self.kidnames = list_dir_only(self.name)
            self.kidnames2 = list_file_only(self.name)
        except:
            self.kidnames = None  # probably permission denied
            self.kidnames2 = None

    def render(self, depth, width):
        return pad('%s%s %s' % (' ' * DIR_DEPTH_MOD * depth, self.icon(),
                                os.path.basename(self.name)), width)

    def children(self):
        if self.kidnames is None: return []
        if self.kids is None:
            self.kids = [Dir(os.path.join(self.name, kid))
                         for kid in self.kidnames]
        return self.kids

    def children2(self):
        if self.kidnames2 is None:
            return []
        x = []
        for i in self.kidnames2:
            n = os.path.join(self.name, i)
            x.append(File(n))
        return x

    def icon(self):
        if self.expanded:
            return '[-]'
        elif self.kidnames is None:
            return '[?]'
        elif self.children():
            return '[+]'
        else:
            return '[ ]'

    def expand(self):
        self.expanded = True

    def collapse(self):
        self.expanded = False

    def traverse(self):
        global PENDING_REFRESH
        yield self, 0
        if not self.expanded: return
        depth = 0
        if PENDING_REFRESH:
            self.refresh()
        for child in self.children():
            for kid, depth in child.traverse():
                yield kid, depth + 1

        for child2 in self.children2():
            yield child2, depth


def inc_err_c(*args):
    global RMT_ERR_C
    RMT_ERR_C += 1


def pend_refresh(val=True):
    global PENDING_REFRESH
    PENDING_REFRESH = val


def remove(*args):
    obj_path: str = PENDING_REMOVE_NAME
    if os.path.isfile(obj_path):
        try:
            os.remove(obj_path)
        except Exception as ex:
            update_header(f"Failed to remove the file ({ex.__class__})")
    else:
        shutil.rmtree(obj_path, onerror=inc_err_c)
        if RMT_ERR_C > 0:
            update_header(f'Encountered errors with removing {RMT_ERR_C} objects')
    _state.add_item("var", "qas", False)
    _state.add_item("var", "qaf", None)
    set_pending_remove_name(None)


def set_pending_remove_name(name): global PENDING_REMOVE_NAME; PENDING_REMOVE_NAME = name


def sx(self: Textbox, ch):
    if ch == 10:
        ns = self.name_s.replace("\\", "/")
        ns = ns.split("/")
        ns.pop(-1)
        fn = os.path.join("/".join(ns), self.text)
        with open(fn, 'w') as file:
            file.write("")
        return True


class FileTree(Window):
    def show(self):
        self.win.keypad(1)
        self.win.nodelay(0)
        curses.curs_set(0)
        mydir = Dir(start)
        mydir.expand()
        curidx = 3
        pending_action = None
        pending_save = False
        pending_newfile = False
        pending_remove = -1

        while self.get_var():
            self.win.clear()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            line = 0
            offset = max(0, curidx - self.height + 3)
            for data, depth in mydir.traverse():
                if line == curidx:
                    self.win.attrset(curses.color_pair(1) | curses.A_BOLD)
                    if pending_action:
                        getattr(data, pending_action)()
                        pending_action = None
                    elif pending_save:
                        return data.name
                else:
                    self.win.attrset(curses.color_pair(0))
                if pending_remove != -1 and pending_remove == line:
                    set_pending_remove_name(data.name)
                    update_header(f"Remove this object?")
                    _state.add_item("var", "qas", True)
                    _state.add_item("var", "qaf", remove)
                    pending_remove = -1
                if 0 <= line - offset < self.height - 1:
                    if pending_newfile and line == curidx:
                        pos = line - offset
                        depth_s = depth
                        name_s = data.name
                        line += 1
                    self.win.addstr(line - offset, 0,
                                    data.render(depth, self.width))
                line += 1
            if pending_newfile and 0 <= line - offset < self.height - 1:
                curses.curs_set(1)
                self.win.attrset(curses.color_pair(0))
                self.win.addstr(pos, 0,
                                " " * self.width)
                self.win.addstr(pos, depth_s * FILE_DEPTH_MOD - 1,
                                "[")
                self.win.addstr(pos, depth_s * FILE_DEPTH_MOD + 1,
                                "]")
                self.win.attrset(curses.color_pair(2))
                self.win.addstr(pos, depth_s * FILE_DEPTH_MOD,
                                "N")
                self.win.refresh()
                tb = Textbox(depth_s * FILE_DEPTH_MOD + 3, pos, -1, 1, "txb", sx)
                tb.name_s = name_s
                tb.edit()
                curses.curs_set(0)
                pending_newfile = False
            self.win.refresh()
            pend_refresh()
            if msvcrt.kbhit():
                ch = self.win.getch()
            else:
                continue
            if ch == get_keybind_act("UP", "ftr"):
                curidx -= 1
            elif ch == get_keybind_act("DOWN", "ftr"):
                curidx += 1
            elif ch == get_keybind_act("PPAGE", "ftr"):
                curidx -= self.height
                if curidx < 0: curidx = 0
            elif ch == get_keybind_act("NPAGE", "ftr"):
                curidx += self.height
                if curidx >= line: curidx = line - 1
            elif ch == get_keybind_act("RIGHT", "ftr"):
                pending_action = 'expand'
            elif ch == get_keybind_act("LEFT", "ftr"):
                pending_action = 'collapse'
            elif ch == get_keybind_act("NEWFILE", "ftr"):
                pending_newfile = True
            elif ch == get_keybind_act("ESCAPE", "ftr"):
                break
            elif ch == get_keybind_act("SELECT", "ftr"):
                pending_save = True
            elif ch == get_keybind_act("REMOVE", "ftr"):
                pending_remove = curidx
            else:
                if bas_input_processor(None, ch):
                    break

            curidx %= line


def main(stdscr: curses.window):
    _state.add_item("scr", "stdscr", stdscr)

    stdscr.clear()
    stdscr.refresh()

    ft = FileTree(0, 0, -1, -1, "ftw")
    ft.focus()
    f = ft.show()


if __name__ == '__main__':
    wrapper(main)
