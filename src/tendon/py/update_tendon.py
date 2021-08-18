from pathlib import Path

from natsort import natsorted
import PySimpleGUIQt as sg
import github as gh
from github.Repository import Repository
import toml

from tendon.py import custom_popups as cp

#pylint: disable=no-member
def eligible_for_update(current_version, min_needed):
    if current_version == min_needed:
        return True
    versions = natsorted([current_version, min_needed])
    if current_version != versions[0]:
        return True
    return False

def save_file(fname: str, new_file):
    with open(fname, 'w') as f:
        f.write(new_file)

def download_folder(repo: Repository, folder_name: str, cwd: str):
    py_dirs = []
    py_files = []
    py_folder = repo.get_contents(f'src/tendon/{folder_name}')
    while py_folder:
        file_content = py_folder.pop(0)
        if file_content.type == 'dir':
            py_dirs.append(file_content.name)
            py_folder.extend(repo.get_contents(file_content.path))
        else:
            py_files.append(file_content)
    for d in py_dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    for f in py_files:
        save_path = f"{cwd}/{f.path.replace('src/tendon/', '')}"
        save_file(save_path, f.decoded_content.decode())

def download_root(repo: Repository, cwd: str):
    root_files = repo.get_contents('')
    for f in root_files:
        if f.type == 'dir':
            continue
        save_path = f"{cwd}/{f.path.replace('src/tendon/', '')}"
        save_file(save_path, f.decoded_content.decode())

def update_app(pyproject: dict):
    cwd = Path.cwd().as_posix()
    print('updating..........')
    repo = gh.Github().get_repo('d-flood/Tendon')
    download_folder(repo, 'py', cwd)
    download_folder(repo, 'resources', cwd)
    download_root(repo, cwd)
    print('done')

def check_for_updates(current_version: str, window: sg.Window):
    g = gh.Github(timeout=5)
    try:
        t = g.get_repo('d-flood/Tendon')
    except:
        cp.ok('Connection timed out. Try again or check your internet connection.', "Can't Connect")
        return
    window.read(timeout=0)
    pyproject = t.get_contents('pyproject.toml')
    pyproject = pyproject.decoded_content.decode()
    pyproject = toml.loads(pyproject)
    min_needed = pyproject['tool']['briefcase']['min_needed_to_update']
    newest_version = (pyproject['tool']['briefcase']['version'])
    if not eligible_for_update(current_version, min_needed):
        cp.ok('There is an update available, but it must be manually installed.\nDownload the newest release at https://github.com/d-flood/Tendon/releases', 'Manual Update Requried')
        return
    versions = [current_version, newest_version]
    versions = natsorted(versions)
    if current_version == newest_version:
        cp.ok('You already have the latest version of Tendon', 'No Updates Available')
    elif current_version == versions[1]:
        cp.ok('Somehow, your version is ahead of the latest release.', 'No Updates Available')
    else:
        if not cp.yes_cancel(f'There is an update available. Do you want to download and update to version {newest_version}?', 'Update Available'):
            return
        update_app(pyproject)
