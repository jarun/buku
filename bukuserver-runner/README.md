# Bukuserver runner

This tool can be used to run and restart Bukuserver, switching databases between runs. It has no third-party dependencies, allowing to run Bukuserver sandboxed in a virtualenv as easily as the system-wide install (which is especifally useful for development).

I suggest installing/symlinking it system-wide (e.g. as an `/usr/local/bin/buku-server` executable). Either of the `*.desktop` files can be edited according to match your setup and installed in your `local/share/applications/` folder for access from system menu.

On Windows, you can create a shortcut file pointing to any Python executable (`python.exe` for windowed mode, `pythonw.exe` for headless) with added CLI arguments: path to `buku-server.py` followed by `--stop-if-running`.

Note that windowed mode may be necessary if you want to see Bukuserver logs, or use noGUI mode (see below). The terminal window can be minimized to tray when not in use, by a program like [KDocker](https://github.com/user-none/KDocker), [RBTray](https://github.com/benbuck/rbtray) or [SmartSystemMenu](https://github.com/AlexanderPro/SmartSystemMenu).

## Usage

When running `buku-server.py` without arguments, it will prompt for database file, then start the Bukuserver. These actions will be repeated once Bukuserver stops running (e.g. after hitting `Ctrl+C`). The script will quit if you cancel the prompt.

In GUI mode, the prompt is implemented as 2 dialogs; a list of databases to choose from, and a text input for creating a new DB. In the shell mode, you can type in DB number from the list, or a new DB name. Note that DB names must be valid filenames in your system (sans the `.db` extension). These files are located in your Buku settings folder (along with the default `bookmarks.db` file).

Running `buku-server.py --stop` will kill the currently running Bukuserver process (thus allowing to restart it in the background, like a daemon). `buku-server.py --stop-if-running` will either start the script or kill Bukuserver if it's running already.

<details><summary><h3>Screenshots</h3></summary>

![DB selection dialog](https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/runner-script/db-selection.png "DB selection dialog")  
_DB selection dialog – shown on startup (unless no DB files were found); initially the previous DB is selected_

![DB creation dialog](https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/runner-script/db-creation.png "DB creation dialog")  
_DB creation dialog – shown if no DB was selected (or none found)_

![DB exists](https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/runner-script/existing-db-confirmation.png "DB exists")  
_A confirmation dialog is shown if new DB name is taken already_

![DB naming error](https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/runner-script/invalid-db-error.png "DB naming error")  
_DB name must be a valid filename, sans the `.db` extension (invalid chars: `/` on Linux, or any of `<>:"/\|?*` on Windows)_

![no-GUI mode](https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/runner-script/non-gui.png "no-GUI mode")  
_DB selection prompt in console shell/no-GUI mode (`BUKU_NOGUI=y`)_
</details>

## Environment variables

The script behaviour can be configured by setting the following environment variables:
* `BUKUSERVER` specifies path to your Bukuserver executable or Buku source directory.
* `BUKU_DEVMODE` – if not empty, Bukuserver will be run in development mode. Normally used with source directory in `BUKUSERVER`.
* `BUKU_VENV` overrides path to your virtualenv sandbox (default depends on whether `BUKU_DEVMODE` is set):
  - when devmode is off, the virtualenv location defaults to a `venv/` folder in your Buku settings directory;
  - when devmode is on, the virtualenv location defaults to a `venv/` folder in the source directory.
* `BUKU_NOGUI` – if not empty, fallback shell prompt will be used (also happens if Tkinter is not present in your Python installation).
* `BUKU_DEFAULT_DBDIR` – specify directory for DB selection (same as Buku itself).

Default values for all of these (as well as for `BUKUSERVER_` options) can be specified in a `bukuserver.env` file in your Buku settings folder:
```sh
# ~/.local/share/buku/bukuserver.env
BUKUSERVER='~/Sources/buku/'  # when running from sources
BUKUSERVER_THEME=slate
BUKUSERVER_DISABLE_FAVICON=false
BUKUSERVER_OPEN_IN_NEW_TAB=true
```
