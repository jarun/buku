## Bukuserver

### Table of Contents

- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [From PyPi](#from-pypi)
  - [From source](#from-source)
- [Webserver options](#webserver-options)
- [Configuration](#configuration)
- [Screenshots](#screenshots)

### Installation

You need to have some packages before you install `bukuserver` on your server.
So be sure to have `python3`, `python3-pip` , `python3-dev`, `libffi-dev` packages from your distribution.

#### Dependencies

```
$ python3 -m pip install --user --upgrade pip
$ python3 -m pip install --user virtualenv
$ python3 -m virtualenv env
$ source env/bin/activate
```

#### From PyPi

    $ pip3 install buku[server]

#### From source

```
$ git clone https://github.com/jarun/Buku
$ cd Buku
$ pip3 install .[server]
```

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
| DB_FILE | full path to db file | path string [default: standard path for buku] |
| DISABLE_FAVICON | disable favicon | boolean [default: `false`] |
| OPEN_IN_NEW_TAB | url link open in new tab | boolean [default: `false`] |

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
<a href="https://i.imgur.com/LozEqsT.png"><img src="https://i.imgur.com/LozEqsT.png" alt="home page" width="650"/></a>
</p>
<p align="center"><i>home page</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/DJUzs1d.png"><img src="https://i.imgur.com/DJUzs1d.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>bookmark stats</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/1eMruZD.png"><img src="https://i.imgur.com/1eMruZD.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>bookmark page</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/W4VUKQV.png"><img src="https://i.imgur.com/W4VUKQV.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>create bookmark</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/213y0Ft.png"><img src="https://i.imgur.com/213y0Ft.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>edit bookmark</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/MQM07VZ.png"><img src="https://i.imgur.com/MQM07VZ.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>view bookmark details</i></a></p>

<p><br><br></p>
<p align="center">
<a href="https://i.imgur.com/0bYgpER.png"><img src="https://i.imgur.com/0bYgpER.png" alt="index page" width="650"/></a>
</p>
<p align="center"><i>tag page</i></a></p>
