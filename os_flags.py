import os


def get_data_store_path(prog_name=None):
    if os.name == "nt":
        data_stg = os.environ["appdata"]
    elif os.name == "posix":
        data_stg = os.environ["HOME"]
    else:
        data_stg = None
    if prog_name is not None and data_stg is not None:
        data_stg = os.path.join(data_stg, prog_name)
    return data_stg


def build_folder_tree(tree, prefix=None):
    for i in tree.keys():
        _ = i
        if prefix is not None:
            i = os.path.join(prefix, _)
        if not os.path.exists(i):
            os.mkdir(i)
        f = tree[_]
        if type(f) == dict:
            build_folder_tree(f, prefix if prefix is not None else None)


def get_bool_flag(name: str):
    return os.environ.get(name) == "true"


def set_bool_flag(name: str, value: bool):
    os.environ[name] = "true" if value else "false"


def get_flag(name: str):
    return os.environ.get(name)


def set_flag(name: str, value: str):
    os.environ[name] = value
