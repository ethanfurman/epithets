#!/usr/bin/env python3.5
"""
a text user interface based on curses
"""
from __future__ import print_function
from aenum import Enum, IntEnum, StrEnum, Flag, auto, NamedTuple
from aenum._enum import global_enum
from collections import deque
from concurrent.futures import Future
from curses import *
import curses
import heapq
import math
import re
from scription import error, print
import select
import sys
from threading import Event as ThreadEvent, Thread, Lock as ThreadLock, current_thread, main_thread, get_ident as thread_ident
import time

## globals

dom_query_cache = {}
main_frame = None
stdscr = None

IntEnum._convert_(
        'Attribute',
        __name__,
        lambda C: C.isupper() and C.startswith('A_'),
        as_global=True,
        )

IntEnum._convert_(
        'ButtonPress',
        __name__,
        lambda C:
            C.isupper() and C.startswith('BUTTON') or
            C in ('ALL_MOUSE_EVENTS','REPORT_MOUSE_POSITION'),
            as_global=True,
        )

IntEnum._convert_(
        'Color',
        __name__,
        lambda C: C.isupper() and C.startswith('COLOR_'),
        as_global=True,
        )

IntEnum._convert_(
        'Misc',
        __name__,
        lambda C: C in ('OK', ),
        as_global=True,
        )

KEY_NULL = 0
KEY_CTRL_A = 1
KEY_CTRL_B = 2
KEY_CTRL_C = 3
KEY_CTRL_D = 4
KEY_CTRL_E = 5
KEY_CTRL_F = 6
KEY_CTRL_G = 7
KEY_CTRL_H = 8
KEY_CTRL_I = 9
KEY_TAB = 9
KEY_CTRL_J = 10
KEY_RETURN = 10
KEY_CTRL_K = 11
KEY_CTRL_L = 12
KEY_CTRL_M = 13
KEY_CTRL_N = 14
KEY_CTRL_O = 15
KEY_CTRL_P = 16
KEY_CTRL_Q = 17
KEY_CTRL_R = 18
KEY_CTRL_S = 19
KEY_CTRL_T = 20
KEY_CTRL_U = 21
KEY_CTRL_V = 22
KEY_CTRL_W = 23
KEY_CTRL_X = 24
KEY_CTRL_Y = 25
KEY_CTRL_Z = 26
KEY_ESC = 27
KEY_FS = 28
KEY_GS = 29
KEY_RS = 30
KEY_US = 31
KEY_SPACE = 32
KEY_BANG = 33
KEY_QUOTE = 34
KEY_HASH = 35
KEY_DOLLAR = 36
KEY_PERCENT = 37
KEY_AMPERSAND = 38
KEY_APOSTROPHE = 39
KEY_LPAREN = 40
KEY_RPAREN = 41
KEY_STAR = 42
KEY_PLUS = 43
KEY_COMMA = 44
KEY_DASH = 45
KEY_PERIOD = 46
KEY_SLASH = 47
KEY_ZERO = 48
KEY_ONE = 49
KEY_TWO = 50
KEY_THREE = 51
KEY_FOUR = 52
KEY_FIVE = 53
KEY_SIX = 54
KEY_SEVEN = 55
KEY_EIGHT = 56
KEY_NINE = 57
KEY_COLON = 58
KEY_SCOLON = 59
KEY_LT = 60
KEY_EQ = 61
KEY_GT = 62
KEY_QUESTION = 63
KEY_AT = 64
KEY_CAP_A = 65
KEY_CAP_B = 66
KEY_CAP_C = 67
KEY_CAP_D = 68
KEY_CAP_E = 69
KEY_CAP_F = 70
KEY_CAP_G = 71
KEY_CAP_H = 72
KEY_CAP_I = 73
KEY_CAP_J = 74
KEY_CAP_K = 75
KEY_CAP_L = 76
KEY_CAP_M = 77
KEY_CAP_N = 78
KEY_CAP_O = 79
KEY_CAP_P = 80
KEY_CAP_Q = 81
KEY_CAP_R = 82
KEY_CAP_S = 83
KEY_CAP_T = 84
KEY_CAP_U = 85
KEY_CAP_V = 86
KEY_CAP_W = 87
KEY_CAP_X = 88
KEY_CAP_Y = 89
KEY_CAP_Z = 90
KEY_LBRACKET = 91
KEY_BACKSLASH = 92
KEY_RBRACKET = 93
KEY_CAROT = 94
KEY_UNDER = 95
KEY_BACKTICK = 96
KEY_A = 97
KEY_B = 98
KEY_C = 99
KEY_D = 100
KEY_E = 101
KEY_F = 102
KEY_G = 103
KEY_H = 104
KEY_I = 105
KEY_J = 106
KEY_K = 107
KEY_L = 108
KEY_M = 109
KEY_N = 110
KEY_O = 111
KEY_P = 112
KEY_Q = 113
KEY_R = 114
KEY_S = 115
KEY_T = 116
KEY_U = 117
KEY_V = 118
KEY_W = 119
KEY_X = 120
KEY_Y = 121
KEY_Z = 122
KEY_LBRACE = 123
KEY_PIPE = 124
KEY_RBRACE = 125
KEY_TILDE = 126

IntEnum._convert_(
        'KeyPress',
        __name__,
        lambda C: C.isupper() and C.startswith('KEY_'),
        as_global=True,
        )

@global_enum
class Border(Enum):
    SINGLE = auto()
    SPACE = auto()


@global_enum
class Orientation(Enum):
    VERTICAL = auto()
    VERT = VERTICAL
    HORIZONTAL = auto()
    HORZ = HORIZONTAL

@global_enum
class Sticky(Flag):
    NORTH = auto()
    SOUTH = auto()
    EAST = auto()
    WEST = auto()
    N = NORTH
    S = SOUTH
    E = EAST
    W = WEST
    NORTH_EAST = N|E
    NORTH_WEST = N|W
    NORTH_SOUTH = N|S
    SOUTH_EAST = S|E
    SOUTH_WEST = S|W
    EAST_WEST = E|W
    NE = N|E
    NW = N|W
    NS = N|S
    SE = S|E
    SW = S|W
    EW = E|W
    NORTH_SOUTH_EAST_WEST = N|S|E|W
    NSEW = N|S|E|W


class Event(NamedTuple):
    pass


class KeyEvent(Event):
    key = 'key press'


class MessageEvent(Event):
    selected = 'choice(s) made', None


class MouseEvent(Event):
    m_id = 'pointer id'
    x = 'x coordinate'
    y = 'y coordinate'
    z = 'z coordinate'
    state = 'mouse state'

class on_key:
    quick_keys = {}
    def __init__(self, *keystrokes):
        self.keys = keystrokes
    def __call__(self, func):
        for key in self.keys:
            self.quick_keys[key] = func
        return func


class Size(NamedTuple):
    height = 0
    width = 1


def set_names(cls):
    """
    Run prop.__set_name__ on class properties in Python 3.5.
    """
    if sys.version_info < (3, 6):
        for name, obj in cls.__dict__.items():
            if getattr(obj, '__set_name__', None):
                obj.__set_name__(cls, name)
    return cls

# Exceptions
class EpithetException(Exception):
    """
    Error
    """

class InsufficientSpace(EpithetException):
    """
    Not enough room for widget.
    """

## helpers

    # Priority (desc)               Example                     Description
    # ---------------               -------                     -----------
    # Inline style                  <h1 style="color: pink;">   Highest priority, directly applied with the style attribute
    # Id selectors                  #navbar                     Second highest priority, identified by the unique id attribute of an element
    # Classes and pseudo-classes    .test, :hover               Third highest priority, targeted using class names
    # Attributes                    [type="text"]               Low priority, applies to attributes
    # Elements and pseudo-elements  h1, ::before, ::after       Lowest priority, applies to HTML elements and pseudo-elements

    # inheritable properties
    # ----------------------
    # border-collapse   border-spacing
    # caption-side      color                   cursor
    # direction         empty-cells
    # font-family       font-size               font-style              font-variant    font-weight     font-size-adjust    font-stretch
    # font
    # letter-spacing    line-height
    # list-style-image  list-style-position     list-style-type         list-style
    # orphans           quotes
    # tab-size
    # text-align        text-align-last         text-decoration-color   text-indent
    # text-justify      text-shadow             text-transform
    # visibility
    # white-space       widows   word-break
    # word-spacing      word-wrap

INHERITABLE = (
        'color', 'cursor', 'empty-cells', 'text-align', 'text-indent', 'text-justify',
        'visibility', 'word-break', 'word-spacing', 'word-wrap',
        )

class Awaitable:
    def __await__(self):
        result = yield 
        return result


async def _coro():  pass
_c = _coro()
Coroutine = type(_c)
_c.close()
del _c, _coro

class CSSProperty:
    """
    handle selection and validation of CSS settings
    """
    def __init__(prop, choices=(), multi=False, sides=0, default=None):
        if choices:
            m_default = None
            if isinstance(choices[0], tuple):
                multi = True
                m_default = tuple(t[0] for t in choices)
            if multi:
                if default is None:
                    default = m_default or choices[0:1]
                prop._set = prop._multi_choice
            else:
                if default is None:
                    default = choices[0]
                prop._set = prop._single_choice
        elif multi:
            prop._set = prop._multi_value

    def __get__(prop, obj, cls=None):
        return getattr(obj, prop.private_name)

    def __set__(prop, obj, *values):
        self._set(obj, *values)

    def __set_name__(prop, cls, name):
        prop.public_name = name
        prop.private_name = '_' + name

    def _multi_choice(prop, obj, *values):
        for v in values:
            if v not in prop.choices:
                raise ValueError('%r not in %r' % (value, prop.choices))
        setattr(obj, prop.private_name, values)

    def _multi_value(prop, obj, *values):
        setattr(obj, prop.private_name, values)

    def _single_choice(prop, obj, value):
        if value not in prop.choices:
            raise ValueError('%r not in %r' % (value, prop.choices))
        setattr(obj, prop.private_name, value)

@set_names
class CSSEntry:
    """
    manage css settings for a widget
    """
    display = CSSProperty(choices=('block', 'none'))
    visibility = CSSProperty(choices=('visible', 'hidden'))
    layout = CSSProperty(choices=('horizontal', 'vertical', 'grid'))
    color = CSSProperty(choices=('white', 'cyan', 'blue', 'yellow', 'red', 'magenta', 'black', 'green'))
    background = CSSProperty(choices=('black', 'blue', 'cyan', 'green', 'magenta', 'red', 'white', 'yellow'))
    text_style = CSSProperty(choices=('normal', 'bold', 'italic', 'strikethrough'), multi=True)
    padding = CSSProperty(sides=4, default=0)
    margin = CSSProperty(sides=4, default=0)
    border = CSSProperty(choices=('none', 'single', 'double'))
    width = CSSProperty(default='auto')
    height = CSSProperty(default='auto')
    min_width = CSSProperty(default=0.0)
    min_height = CSSProperty(default=0.0)
    max_width = CSSProperty(default=1.0)
    max_height = CSSProperty(default=1.0)
    scroll_bar_color = CSSProperty(choices=('white', 'cyan', 'blue', 'yellow', 'red', 'magenta', 'black', 'green'))
    scroll_bar_background_color = CSSProperty(choices=('black', 'blue', 'cyan', 'green', 'magenta', 'red', 'white', 'yellow'))
    scroll_bar_corner_color = CSSProperty(choices=('white', 'cyan', 'blue', 'yellow', 'red', 'magenta', 'black', 'green'))
    content_align = CSSProperty(choices=(('top', 'middle', 'bottom'), ('left', 'center', 'right')))
    text_align = CSSProperty(choices=(('top', 'middle', 'bottom'), ('left', 'center', 'right')))
    grid_size = CSSProperty(sides=2, default=1)
    grid_rows = CSSProperty(multi=True)
    grid_columns = CSSProperty(multi=True)

    def __getitem__(self, name):
        try:
            return getattr(self, name.replace('-','_'))
        except AttributeError:
            raise CSSError('no such setting: %r' % (name, ))

    def __setitem__(self, name, value):
        setting = self[name]
        setting


class CSSError(Exception):
    """
    generic errors with CSS
    """

class CSS:
    """
    handle css for the UI
    """
    def __init__(self, css_text=None):
        self.selectors = {}
        self.classes = {}
        self.elements = {}
        self.css_text = css_text
        if css_text:
            self.parse()

    def __getitem__(self, ids, classes, elements):
        """
        return style properties as dict, or None
        """
        style = {}
        for e in elements:
            for setting, value in self.elements.get(e, {}).items():
                if setting in INHERITABLE:
                    style[setting] = value

    def parse(self):
        """
        get next "word" in css_text
        """
        offset = i = 0
        tokens = []
        while True:
            esc = False
            quote = False
            word = []
            for i, ch in enumerate(self.css_text[offset:]):
                if ch in ' \t\n' and not word:
                    continue
                elif ch in ' \t\n' and word:
                    break
                #
                if word:
                    if ch not in ':;{}':
                        word.append(ch)
                    else:
                        break
                else:
                    word.append(ch)
            tokens.append(''.join(word))
            offset += i or 1
            if offset + 1 >= len(self.css_text):
                break
        error(tokens)
        #
        class SM:
            def __init__(sm_self):
                sm_self.offset = 0
                sm_self._tags = []
                sm_self._values = {}
                sm_self.work = sm_self.get_tags
                while sm_self.offset < len(tokens):
                    sm_self.work()
                if sm_self._tags:
                    error('tags', sm_self._tags)
                    error('values', sm_self._values)
                    raise ValueError('incomplete definition for %r' % ' '.join(sm_self._tags))
            def get_tags(sm_self):
                candidate = tokens[sm_self.offset]
                sm_self.offset += 1
                if candidate != '{':
                    sm_self._tags.append(candidate)
                else:
                    if not sm_self._tags:
                        raise ValueError('missing element/class/id name(s)')
                    sm_self.work = sm_self.get_setting_name
            def get_setting_name(sm_self):
                candidate = tokens[sm_self.offset]
                sm_self.offset += 1
                if candidate == '}':
                    for t in sm_self._tags:
                        if t[0].isalpha():
                            dest = self.elements
                        elif t[0] in '.:':
                            dest = self.classes
                            t = t[1:]
                        elif t[0] == '#':
                            dest = self.selectors
                            t = t[1:]
                        else:
                            raise ValueError('unknown type for %r' % t)

                        entry = dest.setdefault(t, CSSEntry())
                        error('t:', t)
                        error('entry:', entry)
                        for setting, value in sm_self._values.items():
                            error('%r = %r' % (setting, value))
                            entry[setting] = value

                    sm_self.work = sm_self.get_tags
                    sm_self._values = {}
                    sm_self._tags = []
                    sm_self._setting_name = None
                    return
                elif candidate == ':':
                    raise ValueError('missing setting name')
                sm_self._setting_name = candidate.replace('-','_')
                if tokens[sm_self.offset] != ':':
                    raise ValueError('%r missing after %r' % (':', candidate))
                sm_self.offset += 1
                sm_self.work = sm_self.get_setting_values
            def get_setting_values(sm_self):
                values = []
                while sm_self.offset < len(tokens):
                    candidate = tokens[sm_self.offset]
                    sm_self.offset += 1
                    if candidate == ';':
                        break
                    values.append(candidate)
                else:
                    raise ValueError('; missing after %r' % ' '.join(values))
                sm_self._values[sm_self._setting_name] = values
                sm_self._setting_name = None
                sm_self.work = sm_self.get_setting_name
        #
        SM()


def distill(*values):
    res = []
    for value in values:
        if isinstance(value, Enum):
            value = value.value
        res.append(value)
    if len(values) == 1:
        return res[0]
    else:
        return res


class FractionalUnit:
    """
    ratios to split up remaining space
    """
    def __init__(self, value):
        self.value = value
    def __add__(self, fr):
        if not isinstance(fr, self.__class__):
            return NotImplemented
        return self.__class__(self.value + fr.value)
    def __div__(self, fr):
        if not isinstance(fr, (self.__class__, int)):
            return NotImplemented
        if isinstance(fr, self.__class__):
            fr = fr.value
        return self.value / fr

def from_coroutine():
    frame = sys._getframe(1)
    i = 1
    while "looking for a coroutine":
        if frame is None:
            return False
        if frame.f_code.co_flags & 0x180:
            return i
        frame = frame.f_back
        i += 1


class Pipe:
    """
    Two-way communication using Queues
    """
    class PipeQueue:
        def __init__(self, qm, qn):
            self.q1 = qm
            self.q2 = qn
            self.get = qm.get
            self.put = qn.put
            self.task_done = qm.task_done

    def __init__(self):
        one = Queue()
        two = Queue()
        self.conn1 = self.PipeQueue(one, two)
        self.conn2 = self.PipeQueue(two, one)


class Queue:
    """
    handle threading and async queueing
    """
    def __init__(self):
        # print('%d: Queue.__init__()' % thread_ident())
        self.mutex = ThreadLock()
        self.stable = ThreadEvent()
        self.items = deque()
        self.waiting = deque()
        self._closed = False
        self._submitted = 0
        self._finished = 0

    def __repr__(self):
        return 'Queue'

    def close(self):
        # print('%d: Queue.close()' % thread_ident())
        self._closed = True
        with self.mutex:
            if self.waiting and not self.items:
                w = self.waiting.popleft()
                if isinstance(w, Future):
                    w.set_exception(QueueClosed)
                else:
                    sched.ready.append(w)

    def get(self, block=True):
        # error('%d: Queue.get()' % thread_ident())
        if from_coroutine():
            return self.get_async()
        else:
            return self.get_sync(block)

    async def get_async(self):
        while "trying to return an item":
            # error('%d: Queue.get_async() while [%d items]' % (thread_ident(), len(self.items)))
            if not self.items:
                if self._closed:
                    raise QueueClosed()
                self.waiting.append(sched.current)
                sched.current = None
                await switch()
            # error('%d: Queue.get_async() acquiring mutex' % thread_ident())
            with self.mutex:
                # error('%d: Queue.get_async() mutex acquired' % thread_ident())
                try:
                    return self.items.popleft()
                except IndexError:
                    pass

    def get_noblock(self, block):
        # error('%d: Queue.noblock()' % thread_ident())
        with self.mutex:
            if self.items:
                return self.items.popleft(), None
            elif not block:
                return QueueEmpty, None
            else:
                fut = Future()
                self.waiting.append(fut)
                return None, fut

    def get_sync(self, block):
        # error('%d: Queue.get_sync()' % thread_ident())
        item, fut = self.get_noblock(block)
        if fut:
            if main_thread() is current_thread():
                raise Exception("synchronous 'get' on main thread would block event loop")
            # error('%d: Queue.get_sync() waiting for future' % thread_ident())
            item = fut.result()
            # error('%d: Queue.get_sync() future received' % thread_ident())
        return item

    def join(self):
        # print('%d: Queue.join()' % thread_ident())
        self.close()
        # print('%d: Queue.join() waiting' % thread_ident())
        self.stable.wait()
        # print('queue finished')

    def _put(self, item):
        # do the actual work
        with self.mutex:
            self._submitted += 1
            self.stable.clear()
            self.items.append(item)
            if self.waiting:
                w = self.waiting.popleft()
                if isinstance(w, Future):
                    w.set_result(self.items.popleft())
                else:
                    sched.ready.append(w)

    def put(self, item):
        # error('%d: Queue.put(%r)' % (thread_ident(), item))
        if from_coroutine():
            result = self.put_async(item)
        else:
            result = self.put_sync(item)
        return result

    async def put_async(self, item):
        # error('%d: Queue.put_async()' % thread_ident())
        self._put(item)

    def put_sync(self, item):
        # error('%d: Queue.put_sync()' % thread_ident())
        self._put(item)

    def task_done(self):
        # print('%d: Queue.task_done()' % thread_ident())
        # print('  mutex:', self.mutex)
        with self.mutex:
            # print('  mutex acquired')
            self._finished += 1
            # print('  submitted: %d   completed: %d' % (self._submitted, self._finished))
            if self._finished == self._submitted:
                # print('  setting stable')
                self.stable.set()
        # print('  mutex released')

class QueueClosed(Exception):
    pass

class QueueEmpty(Exception):
    pass

class Scheduler:
    """
    Callback scheduler with coroutine support
    """
    def __init__(self):
        self.ready = deque()                    # tasks, callbacks ready to run
        self.sleeping = []                      # await sched.sleep(int)
        self.once = []                          # call_once(int, func)  -- duplicates are ignored
        self.every = {}                         # call_every(int, func)  -- calls func every int seconds
        self.waiting = {}                       # await sched.wait_notify(c_id)
        self.sequence = 0
        self._read_waiting = {}                 # await sched.readable(file_no) | wait_read(file_no, func)
        self._write_waiting = {}                # await sched.writable(file_no) | wait_write(file_no, func)
        self._threads = []                      # sched.new_thread(...)
        self._cleanup = []                      # sched.call_cleanup(func)
        self.current = None
        self.state = 'stopped'

    def call_cleanup(self, func, *args, **kwds):
        error('sched.call_cleanup', func, args, kwds)
        if func is None:
            raise Exception('func cannot be None')
        todo = Todo(func, *args, **kwds)
        error('calling at cleanup: %r' % todo)
        self._cleanup.append(todo)

    def call_every(self, every, func, *args, **kwds):
        error('sched.call_every', func)
        if func is None:
            raise Exception('func cannot be None')
        todo = Todo(func, *args, **kwds)
        self.every[todo] = every
        error('calling every %ss: %r' % (every, todo))
        self.ready.append(todo)

    def call_later(self, delay, func, *args, **kwds):
        error('sched.call_later', delay, func)
        if func is None:
            raise Exception('func cannot be None')
        self.sequence += 1
        deadline = time.time() + delay
        todo = Todo(func, *args, **kwds)
        error('calling in %d seconds: %r' % (delay, todo))
        heapq.heappush(self.sleeping, (deadline, self.sequence, todo))

    def call_soon(self, func, *args, **kwds):
        error('sched.call_soon', func)
        if func is None:
            raise Exception('func cannot be None')
        todo = Todo(func, *args, **kwds)
        error('calling soon: %r' % todo)
        self.ready.append(todo)

    def call_once(self, within, func, *args, **kwds):
        error('sched.call_once', within, func)
        if func is None:
            raise Exception('func cannot be None')
        for todo in self.once:
            if func == todo.func:
                return
        self.sequence += 1
        deadline = time.time() + within
        todo = Todo(func, *args, **kwds)
        error('calling within %d seconds: %r' % (within, todo))
        heapq.heappush(self.once, (deadline, self.sequence, todo))

    def new_task(self, coro, *args, label=None, **kwds):
        error('sched.new_task', label or coro)
        if isinstance(coro, Coroutine):
            if args or kwds:
                raise ValueError('cannot provide arguments when coro is already instanciated [%r, %r, %r]'
                                    % (coro, args, kwds))
            self.ready.append(Task(coro, label=label))
        else:
            self.ready.append(Task(coro(*args, **kwds), label=label))

    def new_thread(self, func, *args, label=None, daemon=False, **kwds):
        error('sched.new_thread', func, label)
        t = Thread(target=func, name=label, daemon=daemon, args=args, kwargs=kwds)
        self._threads.append(t)
        if self.state == 'running':
            t.start()

    def notify(self, c_id, msg):
        error('sched.notify', c_id, msg)
        task = self.waiting[c_id]
        task.input = msg
        self.ready.append(task)

    async def readable(self, fileno):
        error('sched.readable', fileno)
        self._read_waiting[fileno] = sched.current
        sched.current = None
        await switch()
        # error('%d now readable' % fileno)

    def run(self):
        self.state = 'running'
        for t in self._threads[:]:
            t.start()
        while (
                self.state == 'running' and
                (self.ready or self.sleeping or self._read_waiting or self._write_waiting or self.once)
            ):
            if not self.ready:
                if self.sleeping:
                    deadline1, *_ = self.sleeping[0]
                    deadline2, *_ = self.once[0]
                    deadline = min(deadline1, deadline2)
                    timeout = deadline - time.time()
                    if timeout < 0:
                        timeout = 0
                else:
                    timeout = None
                # wait for I/O (and sleep)
                can_read, can_write, _ = select.select(self._read_waiting, self._write_waiting, [], timeout)
                for fd in can_read:
                    self.ready.append(self._read_waiting.pop(fd))
                for fd in can_write:
                    self.ready.append(self._write_waiting.pop(fd))
                # check for sleeping tasks
                now = time.time()
                while self.sleeping:
                    deadline, seq, func = heapq.heappop(self.sleeping)
                    if now < deadline:
                        heapq.heappush(self.sleeping, (deadline, seq, func))
                        break
                    else:
                        self.ready.append(func)
                if not self.ready:
                    # low-priority tasks
                    if self.once:
                        deadline, seq, func = heapq.heappop(self.once)
                        if now < deadline:
                            heapq.heappush(self.once, (deadline, seq, func))
                        else:
                            self.ready.append(func)
            while self.ready:
                func = self.ready.popleft()
                self.current = func
                error('running', func)
                if not isinstance(func, (Task, Todo)):
                    raise TypeError('invalid type for func: %r' % type(func))
                func()
                self.current = None
                if func in self.every:
                    self.call_later(self.every[func], func)
            # error('end of run loop state:', self.state)
        # error('threads:', self._threads)
        self.state = 'stopped'
        for c in self._cleanup:
            c()
        # print('scheduler finished')

    async def sleep(self, delay):
        error('sched.sleep', delay)
        deadline = time.time() + delay
        self.sequence += 1
        heapq.heappush(self.sleeping, (deadline, self.sequence, self.current))
        self.current = None
        await switch()

    async def wait_notify(self, c_id):
        error('sched.wait_notify', c_id)
        self.waiting[c_id] = self.current
        self.current = None
        # error('calling switch()')
        return await switch()
        # error('wait_notify received %r' % (result, ))
        return result

    def wait_read(self, fileno, func):
        error('sched.wait_read', fileno, func)
        self._read_waiting[fileno] = func
    
    def wait_write(self, fileno, func):
        error('sched.wait_write', fileno, func)
        self._write_waiting[file_no] = func

    async def writeable(self, fileno):
        error('sched.writable', fileno)
        self._write_waiting[file_no] = sched.current
        sched.current = None
        await switch()

sched = Scheduler()

def switch():
    return Awaitable()

class Signal:
    """
    send and receive messages
    """
    registry = {}
    #
    def __new__(cls, name=None, doc=None):
        if name not in cls.registry:
            s = object.__new__(cls)
            s.name = name
            s.__doc__ = doc
            s.receivers = []
            if name is None:
                return s
            cls.registry.setdefault(name, s)
        return cls.registry[name]

    def __repr__(self):
        return "Signal(%r)" % self.name

    def connect(self, subscriber):
        self.receivers.append(subscriber)

    def notify(self, event=None, sender=None):
        results = []
        for receiver in self.receivers:
            error('calling', receiver)
            if event is not None:
                res = receiver(event)
            else:
                res = receiver()
            error('notify received %r' % res)
            if isinstance(res, Coroutine):
                error('scheduling returned coro')
                sched.new_task(res)

    def disconnect(self, subscriber):
        try:
            self.receivers.remove(subscriber)
        except ValueError:
            raise ValueError('%r not subscribed to %r' % (subscriber, self)) from None


class Task:
    """
    Run a coroutine as a callback.
    """
    def __init__(self, coro, label=None):
        self.coro = coro
        self.label = label
        self.input = None

    def __call__(self):
        try:
            sched.current = self
            # error('sending %r into %s' % (self.input, self.label))
            self.coro.send(self.input)
            self.input = None
            if sched.current:
                sched.ready.append(self)
        except StopIteration:
            pass

    def __repr__(self):
        if self.label is None:
            return 'Task(%r)' % self.coro
        else:
            return 'Task(%s)' % self.label

class Todo:
    """
    nicer repr for lambdas
    """
    def __init__(self, func, *args, **kwds):
        if isinstance(func, self.__class__):
            kwds = func.kwds
            args = func.args
            func = func.func
        self.func = func
        self.args = args
        self.kwds = kwds

    def __call__(self):
        return self.func(*self.args, **self.kwds)

    def __repr__(self):
        text = repr(self.func)
        if self.args:
            text += ', ' + ', '.join(repr(a) for a in self.args)
        if self.kwds:
            text += ', ' + ', '.join('%s=%r' % (k, v) for k, v in self.kwds.items())
        return "Todo(%s)" % text

## Widgets

    # css variables:
    # min_width, min_height
    # max_width, max_height
    # height, width
    # border
    # fg/bg _color
    # h/v _align
    # h/v _scroll

class Widget:
    """
    base type for other widgets
    """
    #
    calc_best_fit = False              # if True, always call
    css_id = None
    css_class = ()
    css_elements = None
    border_style = None
    _built = False
    _focusable = False
    inner_window = None                 # relative position from origin
    layouts = ()
    modal = False
    _parent = None
    orient = None
    origin = None                   # actual stdscr upper-left corner  (Frames only)
    size = None
    sizes = ()
    sticky = None
    title = None
    _value = None
    visible = True
    #
    def __init__(
            self,
            id=None, css=None, title=None, border=None,
            orient=None, parent=None, origin=None,
            size=None, sticky=None, visible=None,
            **kwds
        ):
        """
        If size is 0, 0 it will be calculated later.
        """
        error(self.__class__.__name__, 'Widget.__init__')
        if title is not None:
            self.title = title
        if border is not None:
            self.border_style = border
        if id is not None:
            if not id or id == '#':
                raise ValueError('id cannot be blank')
            if id[0] != '#':
                id = '#' + id
            if css is not None:
                css = id + ' ' + css
            else:
                css = id
        if css:
            self.css_class = []
            for piece in css.split():
                if piece.startswith('#'):
                    if self.css_id is not None:
                        raise CSSError('too many ids in %r' % css)
                    if id in dom_query_cache:
                        raise ValueError('%r already used by %r' % (id, dom_query_cache[id]))
                    dom_query_cache[id] = self
                    self.css_id = piece
                elif piece.startswith('.'):
                    self.css_class.append(piece)
                else:
                    raise ValueError('%r is neither id nor class' % piece)
        if parent is not None:
            self.parent = parent
            if self is not main_frame:
                self.parent._contained.append(self)
        if origin is not None:
            self.origin = origin
        if orient is not None:
            self.orient = orient
        elif self.orient is None:
            self.orient = HORIZONTAL
        if sticky is not None:
            self.sticky = sticky
        elif self.sticky is None:
            self.sticky = Sticky(0)
        if size is not None:
            self._size = size
        elif self.size is not None:
            self._size = self.size
            self.size = None
        else:
            self._size = 0, 0
        if visible is not None:
            self.visible = visible
        self._contained = []
        if self.border_style:
            self._dfx = 2
            self._dfy = 2
            self.inner_window = 1, 1
        elif self.title:
            self._dfx = 0
            self._dfy = 1
            self.inner_window = 1, 0
        else:
            self._dfx = 0
            self._dfy = 0
            self.inner_window = 0, 0

    def __repr__(self):
        crumbs = []
        widget = self
        while isinstance(widget, Widget):
            crumbs.append(widget.__class__.__name__)
            widget = widget.parent
        value = self.value
        id = self.css_id
        if not value and not id:
            return "<%s: outer=%r, pos=%r>" % ('.'.join(reversed(crumbs)), self.outer_size, self.origin)
        else:
            value = id and str(id) or repr(value) 
            if len(value) > 32:
                value = value[:28] + "...'"
            return "<%s:%s: outer=%r, pos=%r>" % ('.'.join(reversed(crumbs)), value, self.outer_size, self.origin)

    @property
    def outer_size(self):
        height, width = self._size
        width += self._dfx
        height += self._dfy
        return Size(height, width)

    @outer_size.setter
    def outer_size(self, value):
        height, width = value
        width -= self._dfx
        height -= self._dfy
        self._size = height, width

    @property
    def inner_size(self):
        return Size(*self._size)

    @inner_size.setter
    def inner_size(self, value):
        self._size = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        if value is None:
            raise ValueError('cannot set parent to None')
        self._parent = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    def add_char(self, *args):
        """
        add_char([y, x,] ch, [attr])

        Paint character ch at (line, col) with attributes attr.

          y     line number.
          x     column number.
          ch    Character to add.
          attr  Attributes for the character.

        Paint character ch at (line, col) with attributes attr, overwriting any character
        previously painted at that location.  By default, the character position and
        attributes are the current settings for the window object.
        """
        self.window.addch(*args)
        self.window.noutrefresh()

    def add_n_string(self, *args):
        """
        add_n_str([y, x,] str, n, [attr])

        Paint at most n characters of the string.
  
          y     line number.
          x     column number.
          str   String to add.
          n     Maximal number of characters.
          attr  Attributes for characters.
  
        Paint at most n characters of the string str at (line, col) with
        attributes attr, overwriting anything previously on the display.
        By default, the character position and attributes are the
        current settings for the window object.
        """
        self.window.addnstr(*args)
        self.window.noutrefresh()

    def add_string(self, y, x, string, attr=A_NORMAL, origin='window'):
        """
        add_string([y, x,] str, [attr])

        Paint the string.
  
          y     line number.
          x     column number
          str   String to add.
          attr  Attributes for characters.
  
        Paint the string str at (line, col) with attributes attr,
        overwriting anything previously on the display.
        By default, the character position and attributes are the
        current settings for the window object.
        """
        error(self.__class__.__name__, 'Widget.add_string', y, x, string)
        attr = distill(attr)
        wy, wx, _, _ = self.get_wyxd(origin)
        stdscr.addstr(wy+y, wx+x, string, attr)
        stdscr.noutrefresh()

    def attr_off(self, attr):
        """
        Remove attribute attr from the "background" set.
        """
        attr = distill(attr)
        self.window.attroff(attr)

    def attr_on(self, attr):
        """
        Add attribute attr to the "background" set.
        """
        attr = distill(attr)
        self.window.attron(attr)

    def attr_set(self, attr):
        """
        Set the "background" set of attributes.
        """
        attr = distill(attr)
        self.window.attrset(attr)
        self.window.noutrefresh()

    def bkgd(self, ch, attr=A_NORMAL):
        """
        Set the background property of the window.

          ch    Background character.
          attr  Background attributes.
        """
        attr = distill(attr)
        self.window.bkgd(ch, attr)

    def bkgd_set(self, ch, attr=A_NORMAL):
        """
        Set the window's background.

          ch    Background character.
          attr  Background attributes.
        """
        attr = distill(attr)
        self.window.bkgdset(ch, attr)
        self.window.noutrefresh()

    def blur(self):
        error(self.__class__.__name__, 'Widget.blur')
        if self.modal:
            error('    nope')
            return
        if sched.focus is self:
            sched.focus = None
        if self.border_style:
            self.border(attr=curses.color_pair(1)|A_NORMAL)
        else:
            self.paint(attr=curses.color_pair(1)|A_NORMAL)
        stdscr.noutrefresh()
        return self

    def border(self, type=SINGLE, attr=A_NORMAL):
        """
        Draw a border around the edges of the window.

          ls    Left side.
          rs    Right side.
          ts    Top side.
          bs    Bottom side.
          tl    Upper-left corner.
          tr    Upper-right corner.
          bl    Bottom-left corner.
          br    Bottom-right corner.

        Each parameter specifies the character to use for a specific part of the
        border.  The characters can be specified as integers or as one-character
        strings.  A 0 value for any parameter will cause the default character to be
        used for that parameter.
        """
        error(self.__class__.__name__, 'Widget.border')
        attr = distill(attr)
        if type is SPACE:
            ls = rs = ts = bs = tl = tr = bl = br = 32
        elif type is SINGLE:
            ls = rs = ACS_VLINE.value
            ts = bs = ACS_HLINE.value
            tl = ACS_ULCORNER.value
            tr = ACS_URCORNER.value
            bl = ACS_LLCORNER.value
            br = ACS_LRCORNER.value
        else:
            ls = rs = ts = bs = tl = tr = bl = br = type
        y1, x1 = self.origin
        h,  w  = self.outer_size
        y2, x2 = y1+h-1, x1+w-1
        error('  ', y1, x1, '   ', y2, x2)
        stdscr.hline(y1, x1, ts, w, attr)
        stdscr.hline(y2, x1, bs, w, attr)
        stdscr.vline(y1, x1, ls, h, attr)
        stdscr.vline(y1, x2, rs, h, attr)
        stdscr.addch(y1, x1, tl, attr)
        stdscr.addch(y1, x2, tr, attr)
        stdscr.addch(y2, x1, bl, attr)
        try:
            stdscr.addch(y2, x2, br, attr)
        except:
            pass
        stdscr.noutrefresh()

    def build(self, _skip_self=False, **kwds):
        """
        y, x = origin in parent space
        height, width = available space in parent space
        """
        error(self.__class__.__name__, 'Widget.build')
        if not _skip_self:
            # first attempt
            y, x = self.parent.clear_primary
            dy, dx = self.parent.clear_alternate
            h, w = self.parent.inner_size
            ah, aw = h-y, w-x                               # available height|width
            rh, rw = self._size                             # requested height|width
            error('orient: %s   y,x: %r   dy,dx: %r   h,w: %r   ah,aw: %r' % (self.orient, (y,x), (dy,dx), (h,w), (ah,aw)))
            if self.inner_size == (0, 0) or self.calc_best_fit:
                self._calc_best_fit(min(rh, ah), min(rw, aw))
            wh, ww = self.inner_size                        # widget height|width
            bh, bw = self.outer_size                        # aka border size
            if bh > ah or bw > aw:
                # second attempt
                if self.orient is HORIZONTAL:
                    x = dx = 0
                    y = dy
                else: # VERTICAL
                    y = dy = 0
                    x = dx
                ah, aw = h-y, w-x
                if self.inner_size == (0, 0) or self.calc_best_fit:
                    self._calc_best_fit(min(rh, ah), min(rw, aw))
                if bh > ah or bw > aw:
                    raise InsufficientSpace('%r will not fit in %r' % (self, self.parent))
            oy, ox = self.parent.origin
            py, px = self.parent.inner_window
            self.origin = y+oy+py, x+ox+px
            # do we need to increase the size?
            if EAST_WEST in self.sticky:
                bw = aw
            if NORTH_SOUTH in self.sticky:
                bh = ah
            # update size in case sticky changed it
            self.outer_size = bh, bw
            # widget_y, widget_x = self.outer_size
            if self.orient is HORIZONTAL:
                x += bw
                dy = max(dy, y+bh)
            else:  # VERTICAL
                y += bh
                dx = max(dx, x+bw)
            error('orient: %s   y,x: %r   dy,dx: %r' % (self.orient, (y,x), (dy,dx)))
            self.parent.clear_primary = y, x
            self.parent.clear_alternate = dy, dx
        # frame built, now build contained widgets
        error('self:', self)
        self._built = True
        for widget in self._contained:
            if widget.visible:
                error('building', widget)
                widget.build()

    def _calc_best_fit(self, height, width):
        error('_calc_best_fit', height, width)
        h = height
        w = width
        if self.orient is HORIZONTAL:
            layouts = list(self.layouts)
            sizes = list(self.sizes)
        else:   # assume VERTICAL
            layouts = reversed(self.layouts)
            sizes = reversed(self.sizes)
        l, s = None, (1, 1)                         # in case layouts and sizes are not speficied
        for l, s in zip(layouts, sizes):
            if s[0] <= h and s[1] <= w:
                break
        self.inner_size = s
        self.layout = l

    def change_attr(self, *args, ctrl_window=None):
        """
        change_attr([y, x,] [num,] attr)

        Set the attributes of num characters at the current cursor position, or at
        position (y, x) if supplied.

          y     line number.
          x     column number.
          num   Number of cells to update.
          attr  Attributes for the character.
        """
        error('changing attrs with %r on window %r' % (args, ctrl_window))
        if ctrl_window is None:
            ctrl_window = self.window
        ctrl_window.chgat(*args)
        ctrl_window.noutrefresh()

    def clear(self, origin='window'):
        """
        Like erase(), but also cause the whole window to be repainted upon next call
        to refresh().
        """
        error(self.__class__.__name__, 'Widget.clear')
        if self is main_frame:
            stdscr.clear()
        else:
            y, x = self.origin
            h, w = self.outer_size
            error('clear:', y, x, '   ', h, w)
            for y in range(y, y+h):
                stdscr.addstr(y, x, ' '*w)

    def clear_ok(self, flag):
        """
        If flag is True, the next call to refresh() will clear the window completely.
        """
        self.window.clearok()

    def clear_to_bottom(self):
        """
        Erase from cursor to the end of the window: all lines below the cursor are deleted,
        and then the equivalent of clrtoeol() is performed
        """
        self.window.clrtobot()
        self.window.noutrefresh()

    def clear_to_eol(self):
        """
        Erase from cursor to the end of the line.
        """
        self.window.clrtoeol()
        self.window.noutrefresh()

    def cursor_sync_up(self):
        """
        Update the current cursor position of all the ancestors of the window to reflect
        the current cursor position of the window.
        """
        self.window.cursyncup()

    def delete_char(self, y, x):
        """
        Delete any character at (line, col).

          y     line number.
          x     column number.
        """
        self.window.delch(y, x)
        self.window.noutrefresh()

    def delete_line(self):
        """
        Delete the line under the cursor. All following lines are moved up by one line.
        """
        self.deleteln()
        self.window.noutrefresh()

    def dismiss(self, cascade=True):
        error(self.__class__.__name__, 'Widget.dismiss')
        if sched.focus is self:
            sched.focus = None
        for w in self._contained:
            w.dismiss(cascade=False)
        self.visible = False
        self._built = False
        self.window = None
        self.border_window = None
        if cascade:
            error('%r._contained =' % self.parent.__class__.__name__, self.parent._contained)
            if self in self.parent._contained:
                error('removing %r from %r' % (self, self.parent._contained))
                self.parent._contained.remove(self)
            error(self.parent, 'is refreshing')
            self.parent.paint()
            self.parent.refresh()

    def echo_char(self, ch, attr=A_NORMAL):
        """
        Add character ch with attribute attr, and refresh.

          ch    Character to add.
          attr  Attributes for the character.
        """
        attr = distill(attr)
        self.window.echochar(ch, attr)
        self.window.noutrefresh()

    def encloses(self, *args):
        """
        encloses([event] [y, x])

        Return True if the screen-relative coordinates are enclosed by the window.

          event MouseEvent
          y     line number.
          x     column number.
        """
        error(self.__class__.__name__, 'Widget.encloses')
        error(self, args)
        if len(args) == 1:
            event = args[0]
            y, x = event.y, event.x
        else:
            y, x = args
        return bool(self.border_window.enclose(y, x))

    def erase(self):
        """
        Clear window by copying blanks to every cell.
        """
        self.window.erase()
        self.window.noutrefresh()

    def focus(self):
        # make sure currently focused widget is not modal
        error(self.__class__.__name__, 'Frame.focus')
        error('Frame current focus:', sched.focus)
        if sched.focus:
            if sched.focus.modal:
                if not self.is_ancestor(sched.focus):
                    return
            else:
                sched.focus.blur()
        sched.focus = self
        if self.border_style:
            self.border(attr=curses.color_pair(1)|A_BOLD)
        else:
            self.paint(attr=curses.color_pair(1)|A_BOLD)
        error('new focus:', sched.focus)
        stdscr.noutrefresh()
        return self

    def get_beginning_yx(self):
        """
        Return absolute window origin
        """
        error(self.__class__.__name__, 'Widget.get_beginning_yx')
        return self.window.getbegyx()

    def get_bkgd(self):
        """
        Return the window's current background character/attribute pair.
        """
        return self.window.getbkgd()

    def get_char(self, *args):
        """
        get_char([y, x])

        Get a character code from terminal keyboard.

          y     line number.
          x     column number.

        The integer returned does not have to be in ASCII range: function keys,
        keypad keys and so on return numbers higher than 256.  In no-delay mode, -1
        is returned if there is no input, else getch() waits until a key is pressed.
        """
        if args:
            if len(args) != 2:
                raise TypeError('need to specify both y and x, or neither')
        return self.window.getch(*args)

    def get_key(self, *args):
        """
        get_key([y, x])

        Get a character (string) from terminal keyboard.

          y     line number.
          x     column number.

        Returning a string instead of an integer, as get_char() does.  Function keys,
        keypad keys and other special keys return a multibyte string containing the
        key name.  In no-delay mode, an exception is raised if there is no input.
        """
        if args:
            if len(args) != 2:
                raise TypeError('need to specify both y and x, or neither')
        return self.window.getkey(*args)

    def get_max_yx(self):
        """
        Return width and height of window.
        """
        error(self.__class__.__name__, 'Widget.get_max_yx')
        return self.window.getmaxyx()

    def get_parent_yx(self):
        """
        Return origin of window relative to parent.
        """
        error(self.__class__.__name__, 'Widget.get_parent_yx')
        return self.border_window.getparyx()

    def get_string(self):
        """
        Return a string from the keyboard.
        """
        return self.window.getstr()

    def get_wide_char(self, *args):
        """
        get_wide_char([y, x])

        Get a wide character from terminal keyboard.

          y     line number.
          x     column number.

        Return a character for most keys, or an integer for function keys,
        keypad keys, and other special keys.
        """
        if args:
            if len(args) != 2:
                raise TypeError('need to specify both x and y, or neither')
        return self.window.get_wch(*args)

    def get_wyxd(self, origin='window'):
        wy, wx = self.origin
        wh, ww = self.outer_size
        if origin == 'window':
            dy, dx = self.inner_window
            wy += dy
            wx += dx
            wh, ww = self.inner_size
        return wy, wx, wh, ww

    def get_yx(self):
        """
        Return cursor position in window.
        """
        return self.getyx()

    def has_focus(self):
        return sched.focus is self

    def hide(self):
        """
        Remove from parent.
        """
        error(self.__class__.__name__, 'Widget.hide')
        self._built = False
        self.window = None
        self.border_window = None
        self.parent.window.noutrefresh()

    def hline(self, y, x, n, ch=None, attr=A_NORMAL):
        """
        hline([y, x,] ch, n, [attr=_curses.A_NORMAL])

        Display a horizontal line.

          y     Starting line number.
          x     Starting column number.
          n     Line length.
          ch    Character to draw.
          attr  Attributes for the characters.
        """
        if ch is None:
            ch = ACS_HLINE
        attr, ch = distill(attr, ch)
        wy, wx, wh, ww = self.get_wyxd()
        stdscr.hline(y+wy, x+wx, ch, n, attr)
        stdscr.noutrefresh()

    @staticmethod
    def horizontal(rows, cols, size):
        """
        return line, col coordinates column-wise
        """
        for y in range(rows):
            for x in range(cols):
                yield y, x*size

    def immediate_refresh_ok(self, flag):
        """
        If flag is True, any change in the window image automatically causes the window
        to be refreshed; you no longer have to call refresh() yourself. However, it may
        degrade performance considerably, due to repeated calls to wrefresh. This option
        is disabled by default
        """
        self.window.immedok(flag)

    def in_char(self, y, x):
        """
        Return the character at the given position in the window.

          x     X-coordinate.
          y     Y-coordinate.

        The bottom 8 bits are the character proper, and upper bits are the attributes.
        """
        return self.window.inch(y, x)

    def in_string(self, *args):
        """
        in_string([y, x,] [n])

          y     line number.
          x     column number.
          n     maximum number of characters to read

        Return a bytes object of characters, extracted from the window starting at the
        current cursor position, or at y, x if specified. Attributes are stripped from
        the characters. If n is specified, instr() returns a string at most n characters
        long (exclusive of the trailing NUL). The maximum value for n is at least 1023.
        """
        return self.window.instr(*args)

    def insert_char(self, *args):
        """
        insert_char([y, x,] ch, [attr=_curses.A_NORMAL])

        Insert a character before the current or specified position.

          y     line number.
          x     column number.
          ch    Character to insert.
          attr  Attributes for the character.

        All characters to the right of the cursor are shifted one position right, with
        the rightmost characters on the line being lost.
        """
        self.window.insch(*args)
        self.window.noutrefresh()

    def insert_delete_char_ok(self, flag):
        """
        If flag is False, curses no longer considers using the hardware insert/delete
        character feature of the terminal; if flag is True, use of character insertion
        and deletion is enabled. When curses is first initialized, use of character
        insert/delete is enabled by default.
        """
        self.window.idcok(flag)

    def insert_delete_line_ok(self, flag):
        """
        If flag is True, curses will try and use hardware line editing facilities.
        Otherwise, line insertion/deletion are disabled
        """
        self.window.idlok(flag)

    def insert_delete_lines(self, num):
        """
        Insert num lines into the specified window above the current line. The num bottom
        lines are lost. For negative num, delete num lines starting with the one under the
        cursor, and move the remaining lines up. The bottom num lines are cleared. The
        current cursor position remains the same.
        """
        self.window.insdelln(num)
        self.window.noutrefresh()

    def insert_line(self):
        """
        Insert a blank line under the cursor. All following lines are moved down by one line.
        """
        self.window.insertln()
        self.window.noutrefresh()

    def insert_n_strings(self, *args):
        """
        insert_n_string([y, x,] str, n, [attr])

        Insert at most n characters of the string.

          y     line number.
          x     column number.
          str   String to insert.
          n     Maximal number of characters.
          attr  Attributes for characters.

        Insert a character string (as many characters as will fit on the line)
        before the character under the cursor, up to n characters.  If n is zero
        or negative, the entire string is inserted.  All characters to the right
        of the cursor are shifted right, with the rightmost characters on the line
        being lost.  The cursor position does not change (after moving to line, col, if
        specified).
        """
        self.window.insnstr(*args)
        self.window.noutrefresh()

    def insert_string(self, *args):
        """
        insert_string([y, x,] str, [attr])

        Insert the string before the current or specified position.

          y     line number.
          x     column number.
          str   String to insert.
          attr  Attributes for characters.

        Insert a character string (as many characters as will fit on the line)
        before the character under the cursor.  All characters to the right of
        the cursor are shifted right, with the rightmost characters on the line
        being lost.  The cursor position does not change (after moving to line, col,
        if specified).
        """
        self.window.insstr(*args)
        self.window.noutrefresh()

    def is_ancestor(self, widget):
        error(self.__class__.__name__, 'Widget.is_ancestor', widget)
        p = self.parent
        while isinstance(p, Widget):
            error('  checking', p)
            if p is widget:
                return True
            p = p.parent
        return False

    def is_line_touched(self, line):
        """
        Return True if the specified line was modified, otherwise return False.

          line  Line number.

        Raise a curses.error exception if line is not valid for the given window.
        """
        return bool(self.window.is_linetouched(line))

    def is_window_touched(self):
        """
        Return True if the specified window was modified since the last call to
        refresh(); otherwise return False.
        """
        return bool(self.window.is_wintouched())

    def keypad(self, flag):
        """
        If flag is True, escape sequences generated by some keys (keypad, function keys)
        will be interpreted by curses. If flag is False, escape sequences will be left
        as is in the input stream.
        """
        return self.window.keypad(flag)

    def leave_ok(self, flag):
        """
        If flag is True, cursor is left where it is on update, instead of being at “cursor
        position.” This reduces cursor movement where possible. If possible the cursor will
        be made invisible.

        If flag is False, cursor will always be at “cursor position” after an update.
        """
        self.window.leaveok(flag)

    def move_cursor(self, y, x):
        """
        Move cursor to (line, col).
        """
        self.window.move(y, x)
        self.window.noutrefresh()

    def move_window(self, y, x):
        """
        Move the window so its upper-left corner is at (line, col) in its parent window.
        """
        self.window = None
        self.border_window = None
        h, w = self.parent.inner_size
        self.build()
        self.no_update_refresh()

    def next(self):
        """
        cycle forward through focusable elements
        """
        # if self is main_frame or isinstance(self, Frame) and not self._focusable:
        if self is main_frame or self.modal:
            p = self
            contained = self._contained
            i = -1
        else:
            p = self.parent
            contained = p._contained
            i = contained.index(self)
        while "searching for next focus":
            i += 1
            if i >= len(contained):
                if p.modal or p is main_frame:
                    i = 0
                else:
                    contained = p.parent._contained
                    i = contained.index(p)
                    p = p.parent
                    continue
            current = contained[i]
            if current._contained:
                contained = current._contained
                current = contained[0]
                i = 0
                p = current
            if current._focusable:
                break
        if current is not self:
            self.blur()
            current.focus()

    def no_delay(self, flag):
        """
        If flag is True, getch() will be non-blocking.
        """
        self.window.nodelay(flag)

    def no_timeout(self, flag):
        """
        If flag is True, escape sequences will not be timed out.

        If flag is False, after a few milliseconds, an escape sequence will not be
        interpreted, and will be left in the input stream as is.
        """
        self.window.notimeout(flag)

    def no_update_refresh(self):
        """
        noutrefresh([pmincol, pminrow, smincol, sminrow, smaxcol, smaxrow])
        Mark for refresh but wait.

        This function updates the data structure representing the desired state of the
        window, but does not force an update of the physical screen.  To accomplish
        that, call doupdate().
        """
        error(self.__class__.__name__, 'Widget.no_update_refresh')
        stdscr.noutrefresh()

    def paint(self, attr=A_NORMAL, cascade=True):
        """
        Paint self and all contained widgets.
        """
        error(self.__class__.__name__, 'Widget.paint')
        if not self.visible or not self._built:
            return False
        attr = distill(attr)
        self.clear()
        if self.border_style:
            self.border(self.border_style, attr=attr)
        if self.title:
            self.add_string(0, 1, '---| %s |---' % self.title, origin='border', attr=attr)
        error('%s._contained:' % self.__class__.__name__, self._contained)
        if cascade:
            for widget in self._contained:
                if widget.visible:
                    widget.paint(attr=attr, cascade=cascade)

    def prev(self):
        """
        cycle backward through focusable elements
        """
        if self is main_frame:
            p = self
            contained = self._contained
            i = len(contained)
        else:
            p = self.parent
            contained = p._contained
            i = contained.index(self)
        while "searching for previous focusable":
            i -= 1
            if i < 0:
                if p.modal or p is main_frame:
                    i = len(contained) - 1
                else:
                    contained = p.parent._contained
                    i = contained.index(p)
                    p = p.parent
                    continue
            current = contained[i]
            if current._contained:
                contained = current._contained
                current = contained[-1]
                i = len(contained) - 1
                p = current
            if current._focusable:
                break
        if current is not self:
            self.blur()
            current.focus()

    def process_key(self, event):
        """
        process keyboard input

        return False if not handled
        """
        error(self.__class__.__name__, 'Widget.process_key')
        return False

    def process_mouse(self, clicked_widget, event):
        """
        process mouse input

        return False if not handled
        """
        error(self.__class__.__name__, 'Widget.process_mouse')
        return False

    def redraw_line(self, beg, num):
        """
        Mark the specified lines corrupted.

          beg   Starting line number.
          num   The number of lines.

        They should be completely redrawn on the next refresh() call.
        """
        self.window.redrawln(beg, num)

    def redraw_window(self):
        """
        Touch the entire window, causing it to be completely redrawn on the next
        refresh() call.
        """
        self.window.redrawwin()

    def refresh(self):
        """
        Update the display immediately.

        Synchronize actual screen with previous drawing/deleting methods.
        """
        error(self.__class__.__name__, 'Widget.refresh')
        stdscr.refresh()

    def resize(self, lines, cols):
        """
        Reallocate storage for a curses window to adjust its dimensions to the specified
        values. If either dimension is larger than the current values, the window’s data
        is filled with blanks that have the current background rendition (as set by
        bkgdset()) merged into them
        """
        self.window.resize(lines, cols)
        self.window.noutrefresh()

    def scroll(self, *args):
        """
        scroll([lines=1])
        Scroll the screen or scrolling region.

          lines     Number of lines to scroll.

        Scroll upward if the argument is positive and downward if it is negative.
        """
        self.window.scroll(*args)
        self.window.noutrefresh()

    def scroll_ok(self, flag):
        """
        Control what happens when the cursor of a window is moved off the edge of the window
        or scrolling region, either as a result of a newline action on the bottom line, or
        typing the last character of the last line. If flag is False, the cursor is left on
        the bottom line. If flag is True, the window is scrolled up one line. Note that in
        order to get the physical scrolling effect on the terminal, it is also necessary
        to call idlok()
        """
        self.window.scrollok

    def set_scroll_region(self, top, bottom):
        """
        Define a software scrolling region.

          top       First line number.
          bottom    Last line number.

        All scrolling actions will take place in this region.
        """
        self.window.setscrreg(top, bottom)

    def sync_ok(self, flag):
        """
        If flag is True, then syncup() is called automatically whenever there
        is a change in the window
        """
        self.window.syncok(flag)

    def sync_up(self):
        """
        Touch all locations in ancestors of the window that have been changed in the window.
        """
        self.window.syncup()

    def timeout(self, delay):
        """
        Set blocking or non-blocking read behavior for the window.
        If delay is negative, blocking read is used (which will wait indefinitely for input).
        If delay is zero, then non-blocking read is used, and getch() will return -1 if no
           input is waiting.
        If delay is positive, then getch() will block for delay milliseconds, and return -1 if
           there is still no input at the end of that time.
        """
        self.window.timeout(delay)

    def touch_line(self, start, count, changed=True):
        """
        Pretend count lines have been changed, starting with line start.

        If changed is supplied, it specifies whether the affected lines are marked
        as having been changed (changed=True) or unchanged (changed=False).
        """
        self.window.touchline(start, count, changed)

    def touch_window(self):
        """
        Pretend the whole window has been changed, for purposes of drawing optimizations.
        """
        self.window.touchwin()

    def untouch_window(self):
        """
        Mark all lines in the window as unchanged since the last call to refresh().
        """
        self.window.untouchwin()

    @staticmethod
    def vertical(rows, cols, cell_size):
        """
        return line, col coordinates column-wise
        """
        for x in range(cols):
            for y in range(rows):
                yield y, x*cell_size


    def vline(self, *args):
        """
        vline([y, x,] ch, n, [attr=_curses.A_NORMAL])

        Display a vertical line.

          y     Starting line number.
          x     Starting column number.
          ch    Character to draw.
          n     Line length.
          attr  Attributes for the character.
        """
        stdscr.vline(*args)
        stdscr.noutrefresh()


class Frame(Widget):
    """
    holder of other widgets
    """
    modal = False

    def __init__(self, *args, modal=None, **kwds):
        error(self.__class__.__name__, 'Frame.__init__')
        super().__init__(*args, **kwds)
        if modal is not None:
            self.modal = modal
        self.clear_primary = 0, 0                       # both are relative to self.origin
        self.clear_alternate = 0, 0

    def add_widget(self, widget):
        """
        Include widget in size calculation.
        """
        error(self.__class__.__name__, 'Frame.add_widget')
        if isinstance(widget, type):
            widget = widget()
        if widget.parent is None:
            widget.parent = self
            self._contained.append(widget)
        elif widget.parent is not self:
            raise ValueError("widget %r added to %r with a parent of %r" % (widget, self, widget.parent))
        return widget

    def build_contained(self, widget):
        error(self.__class__.__name__, 'Frame.build_contained')
        error('clear primary:', self.clear_primary)
        error('    alternate: ', self.clear_alternate)
        y, x = self.clear_primary
        dy, dx = self.clear_alternate
        lines, cols = self.inner_size
        error('  with', y, x, lines, cols)
        try:
            widget.build(y, x, lines, cols)
        except InsufficientSpace:
            if self.orient is HORIZONTAL:
                x = dx = 0
                lines -= dy - y
                y = dy
            else: # VERTICAL
                y = dy = 0
                cols -= dx - x
                x = dx
            widget.build(y, x, lines, cols)
        # widget successfully drawn on screen
        widget.visible = True
        widget_y, widget_x = widget.outer_size
        if self.orient is HORIZONTAL:
            x += widget_x
            dy = max(dy, y+widget_y)
        else:  # VERTICAL
            y += widget_y
            dx = max(dx, x+widget_x)
        error('orient: %s   y,x: %r   dy,dx: %r' % (self.orient, (y,x), (dy,dx)))
        self.clear_primary = y, x
        self.clear_alternate = dy, dx

class MainFrame(Frame):
    """
    There can be only one.
    """
    _focusable = True
    # status_win = None

    def __init__(self, status=None, **kwds):
        error(self.__class__.__name__, 'MainFrame.__init__')
        global main_frame, stdscr
        if stdscr is not None:
            raise RuntimeError('can only call MainFrame once')
        main_frame = self
        super().__init__(**kwds)
        self.show_status = status

    def __enter__(self):
        # initialize curses
        global ACS, stdscr
        stdscr = curses.initscr()
        ACS = IntEnum._convert_(
                'ACS',
                'curses',
                lambda C: C.isupper() and C.startswith('ACS_'),
                as_global=True,
                )
        globals().update(ACS._member_map_)
        curses.noecho()
        # curses.cbreak()
        curses.raw()
        curses.start_color()
        curses.init_pair(1, COLOR_YELLOW, COLOR_BLACK)
        stdscr.keypad(True)
        stdscr.nodelay(False)
        curses.curs_set(0)
        curses.mousemask(ALL_MOUSE_EVENTS)
        # figure out window sizes
        outer_height, outer_width = stdscr.getmaxyx()
        inner_height, inner_width = outer_height-self._dfy, outer_width-self._dfx
        self.inner_size = inner_height, inner_width
        inner_y, inner_x = self.inner_window
        if self.show_status:
            inner_height -= 2
            self._dfy += 2
            self.inner_size = inner_height, inner_width
            status_win = self.add_widget(StatusLine(size=(2, inner_width), origin=(outer_height-3, inner_x)))
            # self.status_win = StatusLine(size=(2, inner_width), origin=(outer_height-3, inner_x), parent=self)
            Signal('Event').connect(status_win.on_event)
        return self

    def __exit__(self, *args):
        curses.nocbreak()
        stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def build(self):
        error(self.__class__.__name__, 'MainFrame.build')
        height, width = self.inner_size
        self.origin = 0, 0
        super().build(_skip_self=True)
        # if self.status_win is not None:
        #     self.status_win.build()

    def paint(self, attr=A_NORMAL, cascade=True):
        error(self.__class__.__name__, 'MainFrame.paint')
        super().paint(attr=attr, cascade=cascade)
        # if self.status_win is not None:
        #     self.status_win.paint()
        stdscr.refresh()


class Label(Widget):
    """
    line(s) of text to describe another widget
    """
    def __init__(self, text, *args, **kwds):
        error(self.__class__.__name__, 'Label.__init__')
        # error('Label(%r, *%r, **%r)' % (text, args, kwds))
        super().__init__(*args, **kwds)
        self._value = lines = text.split('\n')
        width = max([len(l) for l in lines])
        self.inner_size = len(lines), width

    def paint(self, attr=A_NORMAL, cascade=True):
        """
        paint the Label text in the parent window starting at line, col
        """
        error(self.__class__.__name__, 'Label.paint')
        p = self.parent
        for i, line in enumerate(self.value):
            p.add_string(i, 0, line, attr)
        p.no_update_refresh()


class Entry(Widget):
    """
    enter one line of text
    """
    _focusable = True


class TextBox(Frame):
    """
    enter many lines of text
    """
    _focusable = True
    read_only = False
    cursor = 0, 0
    cursor_state = 1        # 'insert'

    def build(self, *args, **kwds):
        super().build(*args, **kwds)
        self.keypad(True)

    def blur(self):
        self.cursor = self.window.getyx()
        super().blur()

    def focus(self):
        # window.getyx(), window.move()
        # stdscr.move(*self.cursor)
        stdscr.move(5, 10)
        super().focus()
        curses.curs_set(self.cursor_state)

    def paint(self, attr=A_NORMAL, cascade=True):
        error(self.__class__.__name__, 'TextBox.paint')
        super().paint(attr=attr, cascade=cascade)
        if self.value:
            self.add_string(0, 0, self.value, attr)


class Button(Widget):
    """
    send a button-pressed event
    """
    _focusable = True

    def __init__(self, text, *args, on_click, **kwds):
        error(self.__class__.__name__, 'Button.__init__')
        # error('Button(%r, %r, *%r, **%r)' % (text, on_click, args, kwds))
        super().__init__(*args, **kwds)
        self.value = text
        self.on_click = on_click
        self.inner_size = 1, len(text) + 4

    def _activate(self):
        error('on-click =', self.on_click)
        self.focus()
        if isinstance(self.on_click, KeyPress):
            return KeyEvent(self.on_click)
        elif isinstance(self.on_click, Signal):
            error('scheduling', self.on_click.notify)
            sched.call_soon(self.on_click.notify)
        else:
            # better be a Task or Todo!
            sched.ready.append(self.on_click)
        return True

    def paint(self, attr=A_NORMAL, cascade=True):
        error(self.__class__.__name__, 'Button.paint')
        super().paint(attr=attr, cascade=cascade)
        self.add_string(0, 0, ' [%s]' % self.value, attr)
        self.no_update_refresh()

    def process_key(self, event):
        error(self.__class__.__name__, 'Button.process_key')
        # error(self.__class__.__name__, 'is processing', event)
        if event.key in (KEY_SPACE, KEY_RETURN):
            return self._activate()
        return False

    def process_mouse(self, clicked_widget, event):
        error(self.__class__.__name__, 'Button.process_mouse')
        return self._activate()


class CheckBoxes(Frame):
    """
    select any of several options
    """
    calc_best_fit = True
    choices = []
    current = None
    _focusable = True
    _value = []
    _grid = {}

    def __init__(self, *args, choices=None, **kwds):
        error(self.__class__.__name__, 'CheckBoxes.__init__')
        super().__init__(*args, **kwds)
        if choices is not None:
            self.choices = choices
        # build possible sizes
        widths = []
        for c in self.choices:
            widths.append(len(c)+2)     # _o_choice_
        cell_width = self.cell_width = max(widths)
        choices = len(self.choices)
        beginning = []
        mid_point = math.sqrt(choices)
        if int(mid_point) != mid_point:
            mid_point = mid_point + 1
        mid_point = int(mid_point)
        j, k = 1, choices
        while j <= mid_point:
            beginning.append((j, k))
            j += 1
            k, r = divmod(choices, j)
            if r:
                k += 1
        ending = list(reversed([(k, j) for j, k in beginning[:mid_point-1]]))
        if beginning and ending and beginning[-1] == ending[0]:
            beginning.pop()
        self.layouts = beginning + ending
        self.sizes = [(j, k*cell_width) for j, k in self.layouts]

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, choice):
        if choice in self._value:
            self._value.remove(choice)
        else:
            self._value.append(choice)

    def blur(self):
        error(self.__class__.__name__, 'CheckBoxes.blur')
        super().blur()
        self.current = None
        return self

    def focus(self):
        error(self.__class__.__name__, 'CheckBoxes.focus')
        if self.current is None:
            try:
                possible = self.value or self.choices
                if isinstance(possible, (list, tuple)):
                    possible = possible[0]
                self.current = possible
            except IndexError:
                pass
        error('CB.focus() has self.current as %r' % self.current)
        return super().focus()

    def paint(self, attr=A_NORMAL, cascade=True):
        error(self.__class__.__name__, 'CheckBoxes.paint')
        super().paint(attr=attr, cascade=cascade)
        layout = (self.vertical, self.horizontal)[self.orient is HORIZONTAL]
        rows, cols = self.layout
        layout = layout(rows, cols, self.cell_width)
        error('  self.current:', repr(self.current))
        for c in self.choices:
            error('  c = %r' % c)
            current = c == self.current
            selected = c in self.value
            y, x = next(layout)
            c_attr = attr | (A_NORMAL, A_UNDERLINE)[selected]
            if current:
                text = '<%s>' % c
            else:
                text = ' %s ' % c
            self.add_string(y, x, text, c_attr)
            self._grid[(y, x)] = c
            self._grid[c] = y, x
        stdscr.noutrefresh()

    def process_key(self, event):
        error(self.__class__.__name__, 'CheckBoxes.process_key')
        # error(self.__class__.__name__, 'is processing', event)
        c = self.current
        w = self.cell_width
        opts = self._grid
        y, x = opts[c]
        if event.key is KEY_SPACE:
            self.value = self.current
            error(self.value)
            sched.call_soon(Signal(self.__class__.__name__).notify, MessageEvent(selected=self.value))
        elif event.key is KEY_RIGHT:
            if (y, x+w) in opts:
                c = opts[y, x+w]
            else:
                c = opts[y, 0]
        elif event.key is KEY_LEFT:
            if (y, x-w) in opts:
                c = opts[y, x-w]
            else:
                while (y, x+w) in opts:
                    x = x+w
                c = opts[y, x]
        elif event.key is KEY_UP:
            if (y-1, x) in opts:
                c = opts[y-1, x]
            else:
                while (y+1, x) in opts:
                    y += 1
                c = opts[y, x]
        elif event.key is KEY_DOWN:
            if (y+1, x) in opts:
                c = opts[y+1, x]
            else:
                c = opts[0, x]
        else:
            error(event, 'not handled')
            return False # not handled
        self.current = c
        error('self.current is now %r' % c)
        self.paint()
        error('handled')
        return True


class RadioButtons(CheckBoxes):
    """
    select one of several options
    """
    @property
    def value(self):
        return self._value and self._value[0] or ()

    @value.setter
    def value(self, choice):
        if choice not in self._value:
            self._value[:] = [choice]

class CheckBoxEntry(Widget):
    """
    select an option and/or provide a value
    """
    _focusable = True


class Selection(Widget):
    """
    select one of several options from dropdown
    """
    _focusable = True


class Table(Frame):
    """
    display table data
    """

class ProgramStatus(Frame):
    """
    Display status message to user.

    Only call after curses has been initialized.
    """
    border_style = SINGLE
    _focusable = False
    modal = True

    def __init__(self, message, *args, button='Ok', show_button=True, **kwds):
        error(self.__class__.__name__, 'ProgramStatus.__init__')
        super().__init__(*args, **kwds)
        p = kwds.get('parent', main_frame)
        p.add_widget(self)
        self.message = m = self.add_widget(Label(message))
        self.button = b = self.add_widget(Button(button, on_click=Todo(self.dismiss), visible=show_button))
        self.inner_size = 2, max(m.outer_size.width, b.outer_size.width)
        error('ProgramStatus.message.parent:', m.parent)
        error('ProgramStatus.button.parent:', b.parent)
        w, h = self.parent.inner_size
        self.build()
        self.prev_focus = sched.focus.blur()
        error('saved %r as prev_focus' % self.prev_focus)
        self.focus()
        self.paint()
        self.refresh()

    def build(self):
        error(self.__class__.__name__, 'ProgramStatus.build')
        l, c = self.outer_size
        h, w = self.parent.outer_size
        y = (h-l) // 2
        x = (w-c) // 2
        py, px = self.parent.origin
        self.origin = py+y, px+x

    def dismiss(self):
        error('ProgramStatus.dismiss')
        super().dismiss()
        sched.focus = self.prev_focus.focus()
        error('focus returned to', sched.focus)

    def show_button(self):
        error(self.__class__.__name__, 'ProgramStatus.show_button')
        self.button.visible = True
        # self.build_contained(self.button)
        self.build()
        self.button.focus()
        self.button.refresh()


class QueryUser(Frame):
    """
    Ask user a question; return response.
    """
    # _focusable = True
    modal = True

    def __init__(self, question, *args, yes='Yes', no='No', **kwds):
        error(self.__class__.__name__, 'QueryUser.__init__')
        # error('QueryUser(%r, %r, %r, *%r, **%r)' % (question, yes, no, args, kwds))
        super().__init__(*args, **kwds)
        self.question = q = Label(question)
        self.yes = y = Button(yes, on_click=KEY_Y)
        self.no = n = Button(no, on_click=KEY_ESC)
        self.sizes = []
        # first configuration: all on one "line"
        height = max(w.outer_size.height for w in (q, y, n))
        width = sum(w.outer_size.width for w in (q, y, n))
        self.sizes.append(Size(height, width))
        # second configuration: question on one line, yes/no on next line
        height = q.outer_size.height + max(y.outer_size.height, n.outer_size.height)
        width = max(q.outer_size.width, y.outer_size.width+n.outer_size.width)
        self.sizes.append(Size(height, width))
        self.layouts = [HORIZONTAL, VERTICAL]
        self.add_widget(q)
        self.add_widget(y)
        self.add_widget(n)
        error('  QueryUser init()ed')

    def __call__(self):
        error('QueryUser current focus', sched.focus)
        self.prev_focus = sched.focus.blur()
        error('saved %r as prev_focus' % self.prev_focus)
        lines, cols = self.parent.inner_size
        self.build()
        self.focus()
        self.paint()
        self.refresh()

    def build(self):
        error(self.__class__.__name__, 'QueryUser.build')
        if self.inner_size == (0, 0):
            self._calc_best_fit(*self.parent.inner_size)
        if self.layout == HORIZONTAL:
            self.question.sticky = NS
        else:
            self.question.sticky = EW
        # center widget
        l, c = self.outer_size
        h, w = self.parent.outer_size
        y = (h-l) // 2
        x = (w-c) // 2
        py, px = self.parent.origin
        self.origin = py+y, px+x
        error('final size:', self.inner_size)
        super().build(_skip_self=True)

    def paint(self, attr=A_NORMAL, cascade=True):
        error(self.__class__.__name__, 'QueryUser.paint')
        super().paint(attr=attr, cascade=cascade)

    def process_key(self, event):
        error(self.__class__.__name__, 'QueryUser.process_key')
        key = event.key
        if key in (KEY_SPACE, KEY_RETURN):
            if self.yes.has_focus():
                key = KEY_Y
            elif self.no.has_focus():
                key = KEY_C
        if key in (KEY_Y, KEY_CAP_Y):
            sched.state = 'user-quit'
            return True
        elif key in (KEY_ESC, KEY_N, KEY_CAP_N):
            self.dismiss()
            sched.focus = self.prev_focus.focus()
            error('focus returned to', sched.focus)
            sched.focus.refresh()
            return True
        return False
        

class StatusLine(Frame):
    """
    Basic window/app info.
    """
    last_event = None

    def build(self, *args, **kwds):
        error(self.__class__.__name__, 'StatusLine.build')
        # y, x = self.position
        # height, width = self.inner_size
        # self.window = self.border_window = self.parent.border_window.subwin(height, width, y, x)
        # self.window.clear()

    def on_event(self, msg):
        self.last_event = msg
        self.paint()

    def paint(self, attr=A_NORMAL, cascade=True):
        error(self.__class__.__name__, 'StatusLine.paint')
        height, width = self.inner_size
        self.hline(0, 0, width)
        self.add_string(1, 0, "rows: %d,  cols:%d" % stdscr.getmaxyx(), attr)
        self.add_string(1, 25, "color pairs: %d" % curses.COLOR_PAIRS, attr)
        self.add_string(1, 50, "event: %-50r" % (self.last_event, ), attr)
        stdscr.noutrefresh()



## App


class App:
    """
    what the title says
    """
    CSS = CSS()
    css_class = None
    border_style = None
    title = None
    status = None
    initial_focus = None
    layout = ()

    def __init__(self):
        error(self.__class__.__name__, 'App.__init__')
        self.main = main = MainFrame(border=self.border_style, status=self.status, title=self.title, parent=self)
        for name in dir(self):
            if name.startswith('on_'):
                signal_name = ''.join(n.title() for n in name.split('_')[1:])
                error('connecting signal %r to %r' % (signal_name, getattr(self, name)))
                Signal(signal_name).connect(getattr(self, name))
        for widget in self.layout:
            widget = main.add_widget(widget)
            for name in dir(widget):
                if name.startswith('on_'):
                    signal_name = ''.join(n.title() for n in name.split('_')[1:])
                    error('connecting signal %r to %r' % (signal_name, getattr(widget, name)))
                    Signal(signal_name).connect(getattr(widget, name))


    def __repr__(self):
        return "<%s.%s>" % (self.__class__.__name__, __name__)

    @classmethod
    def _compose(cls, widget, path):
        print('_COMPOSE', path)
        widget.css_elements = path
        for name, obj in widget.__class__.__dict__.items():
            if isinstance(obj, type) and issubclass(obj, Widget):
                obj = obj()
                title = getattr(obj, 'title', None)
                css_id = getattr(obj, 'css_id', None)
                if title and not css_id:
                    obj.css_id = title.lower().replace(' ','_')
                cls._compose(obj, cls._path(obj))
                setattr(widget, name, obj)
        print(widget)

    @staticmethod
    def _path(inst):
        path = []
        for obj in inst.__class__.__mro__:
            if issubclass(obj, (App, Widget)):
                name = obj.__qualname__
                if '.' not in name and name not in path and name != 'Widget':
                    path.append(name)
        return path

    def paint(self, attr=A_NORMAL, cascade=True):
        error(self.__class__.__name__, 'App.paint')
        self.main.paint(attr=attr, cascade=cascade)

    def process_key(self, event):
        error(self.__class__.__name__, 'App.process_key')
        # error(self.__class__.__name__, 'is processing', event)
        if event.key in on_key.quick_keys:
            sched.call_soon(on_key.quick_keys[event.key], self)
        elif event.key == KEY_CTRL_Q:
            sched.call_soon(QueryUser('Exit application?', border=SINGLE, parent=self.main))
        elif event.key == KEY_CTRL_C:
            sched.state = 'user-quit'
        elif event.key == KEY_TAB:
            # focus next field/button/whatever
            error('MyApp: moving focus forward')
            sched.focus.next()
        elif event.key == KEY_BTAB:
            # or previous field/button/whatever
            error('MyApp: moving focus backward')
            sched.focus.prev()
        return True

    def process_mouse(self, clicked_widget, event):
        # widget = smallest widget that contains mouse event
        error(self.__class__.__name__, 'App.process_mouse')
        # error('mouse click in', clicked_widget)
        # error('focused: %r   event: %r' % (sched.focus, event))
        if not sched.focus.encloses(event):
            # switch focus
            clicked_widget.focus()
        return True

    async def process_user_input(self, main):
        #
        def find_clicked_widget(widget, fail=False):
            # find smallest widget that contains mouse event
            w = widget
            error('initial widgit:', w)
            contained = w._contained[:]
            error('initial contained:', contained)
            while contained:
                w = contained.pop(0)
                error('checking', w, event)
                if w.encloses(event):
                    contained = getattr(w, '_contained', [])[:]
                    error('narrowing search to:', contained)
                    if not contained:
                        return w
            else:
                # not found anywhere in currently focused widget
                # if not modal, search rest of screen for match
                if fail or widget is self.main:
                    return self.main
                if sched.focus.modal:
                    return False
                return find_clicked_widget(self.main, fail=True)
        #
        while "user hasn't quit":
            ch = stdscr.getch()
            if ch == -1:
                event = None
            elif ch == KEY_MOUSE:
                event = MouseEvent(*curses.getmouse())
            elif ch in KeyPress:
                event = KeyEvent(KeyPress(ch))
            else:
                event = KeyEvent(ch)
            if event is not None:
                name = event.__class__.__name__
                if self.status:
                    sched.call_soon(Signal('Event').notify, event, )
                w = sched.focus
                if isinstance(event, MouseEvent):
                    w = clicked_widget = find_clicked_widget(sched.focus)
                    while w:
                        error('calling %s.process_mouse()' % w)
                        res = w.process_mouse(clicked_widget, event)
                        if res is None:
                            raise ValueError('%s.process_mouse() returned None' % w)
                        elif isinstance(res, Event):
                            event = res
                            break
                        elif res:
                            break
                        w = w.parent
                if isinstance(event, KeyEvent):
                    while w:
                        error('calling %s.process_key()' % w)
                        res = w.process_key(event)
                        if res is None:
                            raise ValueError('%s.process_key() returned None' % w)
                        elif isinstance(res, Event):
                            event = res
                        elif res:
                            break
                        w = w.parent
                if name in Signal.registry:
                    signal = Signal(name)
                    sched.call_soon(signal.notify, event, )
                sched.call_soon(main.refresh)
            await sched.readable(sys.stdin.fileno())

    def query_one(self, id=None, cls=None):
        """
        Search DOM for object with id or cls.
        """
        if cls is None and id is None:
            raise ValueError('either class or css id must be given')
        if cls is not None and id is not None:
            raise ValueError('cannot specify both class and css id')
        target = id or cls
        if target in dom_query_cache:
            return dom_query_cache[target]
        #
        current = self.main
        p = self.main
        contained = []
        i = -1

        while "searching for target":

            if (
                cls is not None and isinstance(current, cls)
                or isinstance(cls, str) and current.__class__.__name__ == cls
                or id is not None and current.css_id == id
                ):
                dom_query_cache[target] = current
                return current

            if current._contained:
                contained = current._contained
                current = contained[0]
                i = 0
                p = current
            else:
                i += 1
                while i >= len(contained):
                    if isinstance(p, App):
                        break
                    contained = p.parent._contained
                    i = contained.index(p) + 1
                    p = p.parent
                else:
                    # end of the road
                    break
                current = contained[i]

        else:
            raise ValueError('unable to find %r' % (cls or id))

    @on_key(KEY_CTRL_R)
    def redraw(self):
        widgets = self.main._contained[:]
        i = 0
        while i < len(widgets):
            # get all the widgets
            f = widgets[i]
            widgets.extend(getattr(f, '_contained', []))
            i += 1
        # hide them
        for w in reversed(widgets):
            w.hide()
            if isinstance(w, Frame):
                w.clear_primary = 0, 0
                w.clear_alternate = 0, 0
        # and rebuild them
        self.main.clear_primary = 0, 0
        self.main.clear_alternate = 0, 0
        self.main.build()
        self.main.paint()
        sched.focus.focus()

    def refresh(self):
        error(self.__class__.__name__, 'App.refresh')
        self.main.refresh()

    def run(self):
        sched.focus = None
        try:
            with self.main as main:
                main.build()
                main.paint()
                # get initially focused widget
                obj = self.initial_focus
                if obj is None:
                    obj = main
                else:
                    obj = self.query_one(cls=obj)
                # and save it on the scheduler
                # sched.focus = obj
                error('focusing', obj)
                obj.focus()
                for w in main._contained:
                    error(repr(w))
                sched.wait_read(sys.stdin.fileno(), Task(self.process_user_input(main), label='process user input'))
                sched.run()
        except KeyboardInterrupt:
            pass


## notes

    # widgets
    #
    # - screen  (stdscr)
    # - frame   (window)
    #
    # - text entry
    # - text box
    # - label
    # - radio buttons
    # - check boxes
    # - selection

if __name__ == '__main__':

    # def cproducer(q):
    #     def _run(n):
    #         if n < 10:
    #             print('contributing', n, flush=True)
    #             q.put(n)
    #             sched.call_later(0.5, lambda: _run(n+1))
    #         else:
    #             print('contributer done', flush=True)
    #     _run(0)
    #
    # async def aproducer(q):
    #     for n in range(10, 20):
    #         print('submitting', n, flush=True)
    #         await q.put(n)
    #         await sched.sleep(0.5)
    #     else:
    #         print('submitter done', flush=True)
    #
    # def tconsumer(q):
    #     try:
    #         for _ in range(10):     # grab ten items
    #             item = q.get()
    #             print('tpc:', item, flush=True)
    #             time.sleep(1)
    #             q.task_done()
    #     except QueueClosed:
    #         print('tpc done', flush=True)
    #
    # async def aconsumer(q):
    #     try:
    #         while "getting items":
    #             item = await q.get()
    #             print('got:', item, flush=True)
    #             await sched.sleep(1)
    #             q.task_done()
    #     except QueueClosed:
    #         print('getter done', flush=True)
    #
    # q = Queue()
    # sched = Scheduler()
    # sched.call_soon(lambda: cproducer(q))
    # sched.new_task(aconsumer, q, label='aconsumer')
    # sched.new_thread(tconsumer, q)
    # sched.new_task(aproducer, q, label='aproducer')
    # sched.call_cleanup(lambda: q.join())
    # print('READY', sched.ready, flush=True)
    # print(sched.sleeping, flush=True)
    # sched.run()

    class EnumButtonBox(CheckBoxes):
        border_style = SINGLE
        choices = ('Attribute', 'Color', 'Misc', 'ButtonPress', 'KeyPress', 'ACS')
        orient= HORIZONTAL
        signals = True
        size = 2, 50
        sticky = EW


    class EnumDisplay(Frame):
        sticky = NSEW
        border_style = SINGLE
        title = 'members'

        def on_enum_button_box(self, msg):
            # msg should be string of selected Enum
            error(msg.selected)
            self.value = [globals()[enum_name] for enum_name in msg.selected]
            self.title = '%d enums' % len(self.value)
            self.paint()

        def paint(self, attr=A_NORMAL, cascade=True):
            super().paint(attr=attr, cascade=cascade)
            iy, ix = self.inner_size
            cols = ix // 40
            rows = iy
            layout = self.vertical(rows, cols, 40)
            if self.value is not None:
                for enum in self.value:
                    error('current enum: %r' % enum)
                    for mbr in enum:
                        try:
                            y, x = next(layout)
                        except StopIteration:
                            break
                        self.add_string(y, x, '%-25s %r' % (mbr.name, mbr.value), attr)
            stdscr.noutrefresh()



    class MyApp(App):
        border_style = SINGLE
        status = True
        title = 'curses Constants'
        initial_focus = EnumButtonBox

        layout = [
                EnumButtonBox,
                EnumDisplay,
                ]

    app = MyApp()
    app.run()



    # with MainFrame(border=True, status=True, title='Alternate Character Set') as main:
    #     main.add_widget(Label("There are %d items in ACS" % len(AlternateCharacterSet)))
    #     main.add_widget(Label("There are %d items in Attribute" % len(Attribute)))
    #     main.add_widget(Label("There are %d items in ButtonEvent" % len(ButtonEvent)))
    #     main.add_widget(Label("There are %d items in KeyEvent" % len(KeyEvent)))
    #     main.add_widget(Label("There are %d items in Color" % len(Color)))
    #     main.add_widget(Label("There are %d items in Misc" % len(Misc)))
    #     for mbr in AlternateCharacterSet:
    #         main.add_widget(Label("%-7s:  %s" % (member.name, member.value)))
    #     main.paint()

        # l.paint(50, 5, parent=main)
        # sw = main.sub_window(90, 30, 57, 3)
        # sw.border()
        # sw.add_string(15, 20, 'something interesting')
        # sw.add_string(3, 7, repr(l))
        # sw.add_string(2, 9, repr(App._path(l)))
        # sw.refresh()
        # curses.doupdate()
        # main.get_char()

