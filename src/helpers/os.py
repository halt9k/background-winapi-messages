from os import chdir
from pathlib import Path
from sys import path


# this module is intended to be imported before all other src/* modules
# allows to keep all the sources organized with working_dir as root:
# working_dir/README.md
# working_dir/<main launch files>
# working_dir/src/*.py
# working_dir/data/*


def ch_project_root_dir():
    this_file_path = Path(__file__).parent
    assert (this_file_path.name == 'helpers')

    new_working_dir = str(this_file_path.parent.parent)

    chdir(new_working_dir)
    # nessesary for imports
    path.append(new_working_dir)

    print(f'Working path is changed to {new_working_dir} \n')


ch_project_root_dir()
