import curses
import curses.ascii
import appstate as state
import msvcrt


def set_var_R(name, val):
    val = not state.get_item("var", name) if val is None else val
    state.add_item("var", name, val)


def get_var_R(name):
    return state.get_item("var", name)


def void(*args): pass


def r_strip_lst(lst):
    return list(map(lambda s: s.rstrip(), lst))


def total_length(lst):
    return sum(map(len, lst))


def cord_to_pos(x, y, text):
    return total_length(text.split()[:y]) + x


class Window:
    def __init__(self, x, y, width, height, statecall):
        self.x = x
        self.y = y
        self.width = width if width > 0 else curses.COLS - self.x
        self.height = height if height > 0 else curses.LINES - self.y

        self._stdscr = state.get_item("scr", "stdscr")
        self._stdscr.clear()
        self._stdscr.refresh()
        self.win = curses.newwin(self.height, self.width, self.y, self.x)
        self.refresh()

        self.statecall = statecall
        state.add_item("scr", self.statecall, self)
        # This is for entering stuff, it is only used by subclasses
        self.set_var(True)

    def msvcrt_kbhit(self):
        # This is used by subclasses
        ch = None
        if msvcrt.kbhit():
            ch = self.win.getch()
        return ch

    def get_var(self):
        return get_var_R(self.statecall)

    def set_var(self, val=None):
        val = not self.get_var() if val is None else val
        set_var_R(self.statecall, val)

    def hline(self, width):
        self.win.hline(curses.ACS_HLINE, width)

    def vline(self, height):
        self.win.vline(curses.ACS_VLINE, height)

    def box(self):
        self.win.box()

    def resize(self, width, height):
        self.width = width - self.x if width > 0 else curses.COLS - self.x
        self.height = height - self.y if height > 0 else curses.LINES - self.y
        try:
            self.win.resize(self.height, self.width)
        except:
            pass

    def reposition(self, x, y):
        self.x = x
        self.y = y
        self.resize(self.width, self.height)
        try:
            self.win.mvwin(self.y, self.x)
        except:
            pass

    def addch(self, ch, attr=0):
        self.win.addch(ch, attr)

    def addstr(self, text, x=None, y=None, attr=None):
        if x is None and y is None:
            if attr:
                self.win.addstr(text, attr)
            else:
                self.win.addstr(text)
        else:
            if attr:
                self.win.addstr(y, x, text, attr)
            else:
                self.win.addstr(y, x, text)

        self.refresh(False)

    def puttext(self, text):
        self.win.erase()
        self.addstr(text)

    def clear(self):
        self.win.clear()
        self.refresh()

    def _getAyx(self):
        return self.win.getyx()

    def _move(self, y, x):
        self.win.move(y, x)

    def abs_move(self, x, y):
        self._move(y, x)
        self.refresh()

    def rel_move(self, x, y):
        self.abs_move(x + self.x, y + self.y)

    def focus(self):
        self._stdscr.move(self._getAyx()[0] + self.y, self._getAyx()[1] + self.x)
        self.refresh()

    def refresh(self, aluo=True):
        self.win.refresh()
        if aluo:
            self._stdscr.refresh()


class Textbox(Window):
    def __init__(self, x, y, width, height, statecall, input_processor=void, auto_proc_input=True, insert_mode=False):
        """
        Creates a TextBox window
        :param x:
        X-position on screen
        :param y:
        Y-position on screen
        :param width:
        Width of the window
        (Set to -1 for max)
        :param height:
        Height of the window
        (Set to -1 for max)
        :param input_processor:
        Function to process input:

        ``function(self, ch: int) -> bool``
        It should take two arguments:
        - self: TextBox (this textbox)
        - ch: int (typed character)
        It should return a bool value, which indicates if the input
        should be cancelled

        :param auto_proc_input:
        Whether to automatically process input which does stuff like
        adding a new character, cursor movements, boundary checks

        :param insert_mode:
        Idk
        """
        super().__init__(x, y, width, height, statecall)
        self.auto_proc_input = auto_proc_input
        self.input_processor = input_processor
        self.insert_mode = insert_mode
        self._update_max_yx()
        self.lastcmd = None
        self.win.keypad(True)
        self._text_buffer = []
        self._frame = (0, self.height)

    @property
    def text(self):
        if len(self._text_buffer) > 1:
            return "\n".join(self._text_buffer)
        else:
            return self._text_buffer[0]

    @text.setter
    def text(self, text):
        self._put_text(text)

    @property
    def mode(self):
        return state.get_item("var", "mode")

    @property
    def stripspaces(self):
        return state.get_item("var", "mode") == "A"

    def _update_max_yx(self):
        maxy, maxx = self.win.getmaxyx()
        self.maxy = maxy - 1
        self.maxx = maxx - 1

    def _end_of_line(self, y):
        self._update_max_yx()
        last = self.maxx
        while True:
            if curses.ascii.ascii(self.win.inch(y, last)) != curses.ascii.SP:
                last = min(self.maxx, last + 1)
                break
            elif last == 0:
                break
            last = last - 1
        return last

    def add_char(self, ch):
        mode = state.get_item("var", "mode")
        if mode == "O":
            self._insert_printable_char(ch)
        else:
            self._insert_printable_char(ch)

    def _insert_printable_char(self, ch):
        self._update_max_yx()
        (y, x) = self._getAyx()
        old_char = None
        while y < self.maxy or x < self.maxx:
            if self.insert_mode:
                old_char = self.win.inch()
            try:
                if self.mode == "O":
                    self.addch(ch)
                else:
                    self.win.insch(ch)
                    y, x = self._getAyx()
                    self._move(y, x + 1)
            except curses.error:
                pass
            if not self.insert_mode or not curses.ascii.isprint(old_char):
                break

    def add_text(self, text):
        for char in text:
            self._insert_printable_char(ord(char))

    def _put_text(self, text):
        self.clear()
        self.add_text(text)

    def _getCyx(self):
        y, x = self._getAyx()
        return y + self._frame[0], x

    def replace_line(self, text):
        y, x = self._getAyx()
        self._move(y, 0)
        for c in text:
            self.addch(ord(c))
        self._move(y, x)

    def deleteline(self):
        self.win.deleteln()
        y, x = self._getAyx()
        if y != 0:
            y -= 1
        self._move(y, self._end_of_line(y))

    def process(self, ch):
        self._update_max_yx()
        (y, x) = self._getAyx()
        self.lastcmd = ch
        if curses.ascii.isprint(ch):
            sd = False
            """if y < self.maxy:
                sd = True
                self.scroll_down()
            if x < self.maxx:
                self._move(y, 0)
                if not sd:
                    self.scroll_down()"""
            self.add_char(ch)
        elif ch in (curses.KEY_LEFT, curses.ascii.BS):
            if x > 0:
                self._move(y, x - 1)
            elif y == 0 and self._getCyx()[0] != 0:
                self.scroll_up()
            elif y > 0 and self.stripspaces:
                self._move(y - 1, self._end_of_line(y - 1))
            elif y > 0:
                self._move(y - 1, self.maxx)
            if ch == curses.ascii.BS:
                self.win.delch()
        elif ch == curses.KEY_RIGHT:  # ^f
            if x < self.maxx:
                # self.addch(32)
                self._move(y, x + 1)
            elif y == self.maxy:
                self.scroll_down()
                self._move(self._getCyx()[1], 0)
            else:
                self._move(y + 1, 0)
        elif ch == curses.ascii.NL:  # ^j
            if y < self.maxy:
                self._move(y + 1, 0)
            else:
                self.scroll_down()
        elif ch == curses.KEY_DOWN:  # ^n
            if y < self.maxy:
                self._move(y + 1, x)
                if x > self._end_of_line(y + 1):
                    self._move(y + 1, self._end_of_line(y + 1))
            else:
                self.scroll_down()
        elif ch == curses.KEY_UP:  # ^p
            if y > 0:
                self._move(y - 1, x)
                if x > self._end_of_line(y - 1):
                    self._move(y - 1, self._end_of_line(y - 1))
            elif self._getAyx()[0] == 0 and self._getCyx()[0] != 0:
                self.scroll_up()

    def scroll_up(self):
        self._frame = self._frame[0] - 1, self._frame[1]
        self.draw_text_buffer()
        self._move(0, self._getAyx()[1])

    def gather_line(self, ln=-1):
        pos = self._getAyx()
        if ln == -1: ln = pos[0]
        res = ""
        for cl in range(self.maxx):
            char = chr(self.win.inch(ln, cl))
            res += char
        self._move(*pos)
        return res.rstrip()

    def scroll_down(self):
        self._frame = self._frame[0] + 1, self._frame[1]
        self.draw_text_buffer()

    def gather(self):
        pos = self._getAyx()
        res = []
        for ln in range(self.maxy if self.maxy > 1 else 1):
            _res = ""
            for cl in range(self.maxx):
                char = chr(self.win.inch(ln, cl))
                _res += char
            res.append(_res)
        self._move(*pos)
        return r_strip_lst(res)

    def write_text_buffer(self):
        text = r_strip_lst(self.gather())
        self._text_buffer[self._frame[0]:self._frame[1]] = text

    def draw_text_buffer(self):
        self._put_text("\n".join(self._text_buffer[self._frame[0]:self._frame[1]]))

    def edit(self):
        self.refresh()
        self.focus()
        while self.get_var():
            if msvcrt.kbhit():
                ch = self.win.getch()
            else:
                continue
            if self.process(ch): break
            if self.input_processor(self, ch):
                break
            self.win.refresh()
            self.write_text_buffer()


class ShellScrollable(Window):
    def __init__(self, x, y, width, height, statecall, scroll):
        self.scroll = scroll

        self.inputs = {}

        super().__init__(x, y, width, height, statecall)

    def add_input(self, ch, fnc):
        self.inputs[ch] = fnc

    def rem_input(self, ch):
        del self.inputs[ch]

    def show(self):
        self.win.keypad(True)
        self.win.nodelay(False)
        curses.curs_set(False)
        curidx = 3

        while self.get_var():
            self.win.clear()
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
            curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
            line = 0
            offset = max(0, curidx - self.height + 3)
            for data, depth in self.scroll.traverse():
                if line == curidx:
                    self.win.attrset(curses.color_pair(1) | curses.A_BOLD)
                else:
                    self.win.attrset(curses.color_pair(0))
                if 0 <= line - offset < self.height - 1:
                    self.win.addstr(line - offset, 0,
                                    data.render(depth, self.width))
                line += 1
            self.win.refresh()
