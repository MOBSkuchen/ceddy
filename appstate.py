GLOBAL_STATE = {}


def add_global_state(name):
    GLOBAL_STATE[name] = {}


def remove_global_state(name):
    del GLOBAL_STATE[name]


def get_global_state(name):
    gs = GLOBAL_STATE.get(name)

    if gs is None: return None

    _ = {}

    for n, obj in gs.items():
        _[n] = str(obj)

    return _


# TODO: check for existence of global state ('gs')

i = 0


def add_item(gs, name, obj):
    GLOBAL_STATE[gs][name] = obj


def rem_item(gs, name):
    del GLOBAL_STATE[gs][name]


def get_item(gs, name):
    return GLOBAL_STATE[gs].get(name)


def init():
    add_global_state("var")
    add_global_state("scr")


init()
