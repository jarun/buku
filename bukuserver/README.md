## Bukuserver

### Table of Contents

- [Installation](#installation)
  - [Installing dependencies](#installing-dependencies)
  - [Installing from PyPi](#installing-from-pypi)
- [Webserver options](#webserver-options)
- [Configuration](#configuration)

### Installation

You need to have some packages before you install `bukuserver` on your server.
So be sure to have `python3`, `python3-pip` , `python3-dev`, `libffi-dev` packages from your distribution.

#### Installing dependencies

```
$ python3 -m pip install --user --upgrade pip
$ python3 -m pip install --user virtualenv
$ python3 -m virtualenv env
$ source env/bin/activate
$ git clone https://github.com/jarun/Buku
$ cd Buku
$ pip3 install .[server]
```

#### Installing from PyPi

    $ pip3 install buku[server]

### Webserver options

To run the server on host 127.0.0.1, port 5001, run following command:

    $ bukuserver run --host 127.0.0.1 --port 5001

Visit `127.0.0.1:5001` in your browser to access your bookmarks.

See more option on `bukuserver run --help` and `bukuserver --help`

### Configuration

Following are available os env config available for bukuserver.

| Name (without prefix) and description | Value |
| --- | --- |
| PER_PAGE (bookmarks per page) | positive integer [default: 10] |
| SECRET_KEY (server secret key) | string [default: os.urandom(24)] |
| URL_RENDER_MODE (url render mode) | `full` or `netloc` [default: `full`] |

Note: `BUKUSERVER_` is the common prefix.

Note: if input is invalid, the default value will be used

e.g. to set bukuserver to show 100 item per page run the following command

```
# on linux
$ export BUKUSERVER_PER_PAGE=100

# on windows
$ SET BUKUSERVER_PER_PAGE=100
```
