import os
import os.path
import sys


def get_module_paths():
    for module in sys.modules.values():
        path = getattr(module, '__file__', None)
        if not path:
            continue

        if path.endswith('.pyc'):
            path = path[:-1]

        if not os.path.exists(path):
            continue

        yield path


def get_changed_generator():
    mtimes = {}

    while 1:
        changes = set()
        for path in get_module_paths():
            mtime = os.path.getmtime(path)
            previous_mtime = mtimes.get(path)

            if previous_mtime and mtime != previous_mtime:
                changes.add(path)

            if not previous_mtime:
                mtimes[path] = mtime

        yield changes
