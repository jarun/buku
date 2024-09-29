#!/usr/bin/env python
# Usage: `buku-server.py` starts up the server, `buku-server.py --stop` sends TERM to the already running server
#        `buku-server.py --stop-if-running` will either start the script or kill Bukuserver if it's running already
from signal import signal, SIGINT
from contextlib import contextmanager
from os import environ as env
import sys
import os
import re
import shlex
import csv
import venv
import subprocess

TITLE = re.sub(r'\.py$', '', os.path.basename(__file__))
IS_WINDOWS = sys.platform == 'win32'

is_path = lambda s: ('/' in s or os.sep in s or s in ('.', '..'))
in_venv = lambda virtualenv, name: os.path.join(virtualenv, ('Scripts' if IS_WINDOWS else 'bin'), name)
set_title = lambda s: (print(f'\033]2;{s}\007', end='') if not IS_WINDOWS else run(f'title {s}', shell=True))

try:
    from tkinter.messagebox import showerror, askyesno
    from tkinter.simpledialog import askstring, Dialog
    from tkinter import ttk
    import tkinter as tk

    class QueryList(Dialog):
        def __init__(self, title, prompt, values, initial=None, parent=None):
            self._prompt, self._vals, self._initial = prompt, values, (initial if initial in values else values[0])
            super().__init__(parent, title)

        def body(self, master):
            w = ttk.Label(master, text=self._prompt, justify=tk.LEFT)
            w.grid(row=0, padx=5, sticky=tk.W)
            self._list = ttk.Treeview(master, show='tree')
            self._list.grid(row=1, padx=5, sticky=tk.W+tk.E)
            scroll = ttk.Scrollbar(master)
            scroll.grid(row=1, padx=5, sticky=tk.E+tk.N+tk.S)
            self._list.config(yscrollcommand=scroll.set)
            scroll.config(command=self._list.yview)
            self._keys = [self._list.insert('', 'end', text=s) for s in self._vals]
            self.select(self._vals.index(self._initial))
            self._list.bind('<KeyPress>', self.onkeypress)
            self._list.bind('<Double-1>', lambda _: self.after('idle', self.ok))
            return self._list

        def select(self, index):
            self._list.see(self._keys[index])
            self._list.focus(self._keys[index])
            self._list.selection_set(self._keys[index])

        def onkeypress(self, evt):
            match = [i for i, s in enumerate(self._vals) if s.startswith(evt.char)]
            if evt.char and match:
                cur = self._list.index(self._list.focus())
                self.select(cur+1 if self._vals[cur].startswith(evt.char) and cur+1 in match else match[0])

        def validate(self):
            self.result = self._list.item(self._list.focus())['text']
            return True

    asklist = lambda title, prompt, values, initial=None: QueryList(title, prompt, values, initial=initial).result
    GUI = True
except ImportError:
    GUI = False
    print('Failed to initialize GUI', file=sys.stderr)

def is_valid_filepath(path):
    try:
        os.lstat(path)
    except FileNotFoundError:
        pass
    except Exception:
        return False
    if os.path.isdir(path) or path.endswith(os.path.sep):
        return False  # directory
    drive, s = os.path.splitdrive(path)
    return not IS_WINDOWS or not re.search(r'[<>:"|?*]', s)

@contextmanager
def ignore_interrupt():  # temporarily disables raising KeyboardInterrupt on Ctrl+C
    old_handler = signal(SIGINT, lambda sig, frame: None)
    yield
    signal(SIGINT, old_handler)

def run(command, *, shell=IS_WINDOWS, check=True):
    try:
        command = (os.path.expandvars(command) if isinstance(command, str) else [os.path.expandvars(s) for s in command])
        with ignore_interrupt():
            return subprocess.run(command, shell=shell, check=check)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)

def parse_csv(text):
    text = (text.decode() if isinstance(text, bytes) else str(text)).strip()
    keys, lines = None, re.split(r'[\r\n]+', text)
    for row in csv.reader(lines):
        if not keys:
            keys = row
        else:
            yield dict(zip(keys, row))

def find_process(query, regex):
    if IS_WINDOWS:
        query = str(query or "name LIKE '%'")
        command = ['wmic', 'process', 'where', query, 'get', 'commandline,processid', '/format:csv']
        output = subprocess.check_output(command, shell=True)
        for process in parse_csv(output):
            if re.search(regex, process['CommandLine']):
                return int(process['ProcessId'])
    else:
        command = 'ps x -o pid,cmd | awk ' + shlex.quote(f'$2 ~ /{query or ".*"}/')
        output = subprocess.check_output(command, shell=True)
        for line in output.decode().splitlines():
            pid, cmdline = line.lstrip().split(' ', 1)
            if re.search(regex, cmdline):
                return pid
    return None  # nothing found

def find_bukuserver_process():
    if not IS_WINDOWS:
        return find_process(r'(^|\/)python[.0-9]*$', r'\b(bukuserver(/server\.py)?) run$')
    return find_process('name like "python%.exe"', r'\b(bukuserver-script\.py|bukuserver([/\\]server\.py)?)"? run$')

def kill_process(pid):
    run(['kill', str(pid)] if not IS_WINDOWS else ['taskkill', '/F', '/pid', str(pid)])

def get_buku_config_dir():
    path = (env.get('APPDATA') if IS_WINDOWS else
            env.get('XDG_DATA_HOME') or os.path.join(os.path.expanduser('~'), '.local', 'share'))
    return os.path.join(path, 'buku')

def read_env_file(path):
    regex = re.compile('([_A-Z]+)=(?:"(.*)"|\'(.*)\'|(.*))')
    try:
        with open(path, encoding='utf-8') as fin:
            for line in fin:
                tokens = shlex.split(line, comments=True)
                if tokens and (m := regex.fullmatch(tokens[0])):
                    yield (m[1], m[2] or m[3] or m[4])
    except FileNotFoundError:
        pass


def selectdb(confdir, old=None, gui=GUI, title=TITLE):
    old = old and re.sub(r'^' + re.escape(confdir+os.path.sep), '', re.sub(r'\.db$', '', old))
    if old and any(c in old for c in ['/', os.path.sep]):
        old = None
    dbs = sorted(s[:-3] for s in os.listdir(confdir) if s.lower().endswith('.db'))
    if gui:
        db = (None if not dbs else
              asklist(title, 'Choose DB (or click Cancel to create new DB)', dbs, initial=old or 'bookmarks'))
        while not db:
            db = askstring(title, f'{"Create new DB?":65}', initialvalue=old or 'bookmarks')
            if db is None:
                print('No name given, qutting', file=sys.stderr)
                return None
            dbfile = os.path.join(confdir, db+'.db')
            if not db or any(c in db for c in ['/', os.path.sep]) or not is_valid_filepath(dbfile):
                showerror(title, f'Invalid DB name: "{db}"')
                db = None
            elif os.path.exists(dbfile):
                if not askyesno(title, f'"{db}" exists already. Open anyway?'):
                    db = None
    else:
        db = None
        while not db:
            try:
                print('\nType DB name or index (0 to quit):')
                for idx, name in enumerate(dbs, start=1):
                    print(f'{idx}. {name}')
                try:
                    db = input('> ' if not old else f'> [{old}] ').strip() or old or 'bookmarks'
                except EOFError as e:
                    raise KeyboardInterrupt from e
            except KeyboardInterrupt:
                with ignore_interrupt():
                    print()
                    print('Input cancelled', file=sys.stderr)
                    return None
            try:
                idx = int(db)
                if idx == 0:
                    print('Entered "0", quitting', file=sys.stderr)
                    return None
                if idx > 0:
                    db = dbs[idx-1]
                    break
            except IndexError:
                print('No such index!', file=sys.stderr)
                db = None
                continue
            except ValueError:
                pass  # not an index
            dbfile = os.path.join(confdir, db+'.db')
            if not db or any(c in db for c in ['/', os.path.sep]) or not is_valid_filepath(dbfile):
                print(f'Invalid DB name: "{db}"', file=sys.stderr)
                db = None
            elif not os.path.exists(dbfile):
                if input(f'"{db}" does not exist yet. Create? [Y/n] ').upper().strip() == 'N':
                    db = None
    return db and os.path.join(confdir, db+'.db')

def load_virtualenv(virtualenv, devmode=False, reinstall=False):
    print(f'Using {os.path.abspath(virtualenv)}')
    venv.create(virtualenv, with_pip=True, prompt='buku')
    run([in_venv(virtualenv, 'python'), '-m', 'pip', 'install', '--upgrade', 'pip'])
    if reinstall:
        env.get('BUKUSERVER_LOCALE') and run([in_venv(virtualenv, 'pip'), 'install', 'flask-babel'])
        if not devmode:
            run([in_venv(virtualenv, 'pip'), 'install', '.[server]'])
        else:
            run([in_venv(virtualenv, 'pip'), 'install', '--editable', '.[server]'])

def prepare_vars():
    confdir = get_buku_config_dir()
    for name, value in read_env_file(os.path.join(confdir, 'bukuserver.env')):
        print(f'default:{name}={shlex.quote(value)}')
        env.setdefault(name, value)
    workdir, exec, devmode = None, env.get('BUKUSERVER') or '', bool(env.get('BUKU_DEVMODE'))
    devmode and env.setdefault('BUKUSERVER_DEBUG', 'true')
    if exec and os.path.isdir(os.path.expanduser(exec)):
        workdir, exec = exec, os.path.join('bukuserver', 'server.py')
    return {
        'confdir': confdir,
        'devmode': devmode,
        'gui': GUI and not env.get('BUKU_NOGUI'),
        'exec': exec or 'bukuserver',
        'workdir': workdir,
        'virtualenv': env.get('BUKU_VENV') or (workdir and os.path.join(('.' if devmode else confdir), 'venv')),
    }

def run_repeatedly(confdir, devmode=False, gui=GUI, exec=None, workdir=None, virtualenv=None):
    if workdir:
        os.chdir(os.path.expanduser(workdir))
    elif virtualenv:
        os.chdir(os.path.expanduser(virtualenv))
        virtualenv = '.'
    set_title(TITLE)
    virtualenv and load_virtualenv(virtualenv, devmode=devmode, reinstall=bool(workdir))
    command = [os.path.expanduser(exec), 'run']
    if exec.endswith('.py'):
        command = ['python'] + command
    elif exec == 'bukuserver':
        command = ['python', '-m'] + command
    if virtualenv:
        command[0] = in_venv(virtualenv, command[0])
    set_title(f'{TITLE} [{shlex.join(command)}]')
    db = env.get('BUKUSERVER_DB_FILE') or os.path.join(confdir, 'bookmarks.db')
    while True:
        print('Running Bukuserver…')
        if not (db := selectdb(confdir, gui=gui, old=db)):
            break
        env['BUKUSERVER_DB_FILE'] = db
        print(f'BUKUSERVER_DB_FILE={db}')
        run(command, check=False)

if __name__ == '__main__':
    if (pid := find_bukuserver_process()):
        if any(s in sys.argv for s in ['--stop', '--stop-if-running']):
            print(f'Killing process {pid}')
            kill_process(pid)
            sys.exit()
        else:
            print('Already running bukuserver!', file=sys.stderr)
            sys.exit(1)
    if '--stop' in sys.argv:
        print('Could not find a running bukuserver process!', file=sys.stderr)
        sys.exit(1)
    run_repeatedly(**prepare_vars())
