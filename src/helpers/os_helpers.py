from os import chdir
from pathlib import Path
from sys import path

"""
 This module is intended to be imported before all other modules.
 Allows to keep working dir consistent both when start from ./run.bat and ./src/main.py
  For example, surces are organized with working dir . as root:
 ./README.md
 ./run.bat
 ./src/*.py
 ./src/helpers/os_helpers.py
 ./data/*

 Import without warning:
 from src.helpers import os_helpers  # noqa: F401
"""


def ch_project_root_dir():
    this_file_path = Path(__file__).parent
    assert this_file_path.name == 'helpers'

    src_dir = this_file_path.parent
    assert src_dir.name == 'src'

    project_dir = str(src_dir.parent)
    src_dir = str(src_dir)

    chdir(project_dir)

    if src_dir in path:
        # ambigious imports can be broken
        path.remove(src_dir)
    if src_dir in path:
        # ambigious imports can be broken, dupe remove is nessesary somethimes
        path.remove(src_dir)
    assert src_dir not in path

    if project_dir not in path:
        path.append(project_dir)

    print(f'Working path is changed to {project_dir} \n')


ch_project_root_dir()
