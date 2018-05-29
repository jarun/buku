## Bukuserver

### Table of Contents

- [Installation](#installation)
  - [Installing dependencies](#installing-dependencies)
  - [Installing from PyPi](#installing-from-pypi)
- [Webserver options](#webserver-options)
- [Configuration](#configuration)
- [Screenshots](#screenshots)

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

| Name (without prefix) | Description | Value |
| --- | --- | --- |
| PER_PAGE | bookmarks per page | positive integer [default: 10] |
| SECRET_KEY | server secret key | string [default: os.urandom(24)] |
| URL_RENDER_MODE | url render mode | `full` or `netloc` [default: `full`] |

Note: `BUKUSERVER_` is the common prefix.

Note: if input is invalid, the default value will be used

e.g. to set bukuserver to show 100 item per page run the following command

```
# on linux
$ export BUKUSERVER_PER_PAGE=100

# on windows
$ SET BUKUSERVER_PER_PAGE=100

# in dockerfile
ENV BUKUSERVER_PER_PAGE=100
```

### Screenshots

<p><br></p>
<p align="center">
<a href="https://i.imgur.com/EELmkRU.png"><img src="https://i.imgur.com/EELmkRU.png" alt="home page" width="650"/></a>
</p>
<p align="center"><i>home page</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/MBgdf6L.png"><img src="https://i.imgur.com/MBgdf6L.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>bookmark stats</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/tnRWsds.png"><img src="https://i.imgur.com/tnRWsds.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>bookmark page (1)</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/W5onldC.png"><img src="https://i.imgur.com/W5onldC.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>bookmark page (2)</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/ONW70gy.png"><img src="https://i.imgur.com/ONW70gy.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>bookmark edit page</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/ohctZyu.png"><img src="https://i.imgur.com/ohctZyu.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>tag page</i></a></p>
