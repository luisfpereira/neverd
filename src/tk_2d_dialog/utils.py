
def flatten_list(ls):
    new_list = []
    for ls_ in ls:
        new_list.extend(ls_)

    return new_list


def get_root(widget):
    parent = widget
    while True:
        if parent.master is None:
            return parent
        parent = parent.master
