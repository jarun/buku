## Bukuserver

### Table of Contents

- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [From PyPi](#from-pypi)
  - [From source](#from-source)
  - [Using Docker](#using-docker)
  - [Using Docker Compose](#using-docker-compose)
- [Webserver options](#webserver-options)
- [Configuration](#configuration)
- [Screenshots](#screenshots)

### Installation

You need to have some packages before you install `bukuserver` on your server.
So be sure to have `python3`, `python3-pip` , `python3-dev`, `libffi-dev` packages from your distribution.

#### Dependencies

```
$ # venv activation (for development)
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install --upgrade pip
```

#### From PyPi

```sh
$ # regular/venv install
$ pip3 install "buku[server]"
$ # pipx install
$ pipx install "buku[server]"
```

#### From source

```sh
$ git clone https://github.com/jarun/buku
$ cd buku
$ # regular/venv install
$ pip3 install ".[server]"
```

#### Using Docker

To build the image execute the command from the root directory of the project:

```sh
docker build -t bukuserver .
```

To run the generated image.

```sh
docker run -it --rm -v ~/.local/share/buku:/root/.local/share/buku -p 5001:5001 bukuserver
```

All the data generated will be stored in the `~/.local/share/buku` directory.
Feel free to change it to the full path of the location you want to store the
database.

Visit `127.0.0.1:5001` in your browser to access your bookmarks.

#### Using Docker Compose

There is a `docker-compose.yml` file present in the `docker-compose` directory
in the root of this project. You may modify the configurations in this file to
your liking, and then simply execute the below command.

```sh
docker-compose up -d
```

You will have you bukuserver running on port port 80 of the host.

To stop simply run

```sh
docker-compose down
```

In case you want to add basic auth to your hosted instance you may do so by
creating a `.htpasswd` file in the `data/basic_auth` directory. Add a user to
the file using

```sh
htpasswd -c data/basic_auth/.htpasswd your_username
```

And then comment out the basic auth lines from the `data/nginx/nginx.conf` file.

For more information please refer the [nginx docs](https://docs.nginx.com/nginx/admin-guide/security-controls/configuring-http-basic-authentication/).

### Webserver options

To run the server on host 127.0.0.1, port 5001, run following command:

    $ bukuserver run --host 127.0.0.1 --port 5001

Visit `127.0.0.1:5001` in your browser to access your bookmarks.

See more option on `bukuserver run --help` and `bukuserver --help`

### Configuration

The following are os env config variables available for bukuserver.

| Name (_without prefix_) | Description | Value |
| --- | --- | --- |
| PER_PAGE | bookmarks per page | positive integer [default: 10] |
| SECRET_KEY | [flask secret key](https://flask.palletsprojects.com/config/#SECRET_KEY) | string [default: os.urandom(24)] |
| URL_RENDER_MODE | url render mode | `full` or `netloc` [default: `full`] |
| DB_FILE | full path to db file | path string [default: standard path for buku] |
| READONLY | read-only mode | boolean [default: `false`] |
| DISABLE_FAVICON | disable bookmark [favicons](https://wikipedia.org/wiki/Favicon) | boolean [default: `true`] ([here's why](#why-favicons-are-disabled-by-default))|
| OPEN_IN_NEW_TAB | url link open in new tab | boolean [default: `false`] |
| REVERSE_PROXY_PATH | reverse proxy path | string |
| THEME | [GUI theme](https://bootswatch.com/3) | string [default: `default`] (`slate` is a good pick for dark mode) |
| LOCALE | GUI language (partial support) | string [default: `en`] |

Note: `BUKUSERVER_` is the common prefix (_every variable starts with it_).

Note: Valid boolean values are `true`, `false`, `1`, `0` (case-insensitive).

Note: if input is invalid, the default value will be used if defined

Note: `BUKUSERVER_LOCALE` requires either `flask_babel` or `flask_babelex` installed

e.g. to set bukuserver to show 100 item per page run the following command

```
# on linux
$ export BUKUSERVER_PER_PAGE=100

# on windows
$ SET BUKUSERVER_PER_PAGE=100

# in dockerfile
ENV BUKUSERVER_PER_PAGE=100
```

Note: the value for BUKUSERVER_REVERSE_PROXY_PATH
is recommended to include preceding slash and not have trailing slash
(i.e. use `/foo` not `/foo/`)

#### Why favicons are disabled by default

At Bukuserver, we have [disabled favicon as a default setting](#configuration) in order to prevent any non-user triggered network activity.

Our favicon is generated with the assistance of Google.

It is important to be aware that favicon has the potential to be used for browser fingerprinting,
a technique used to identify and track a person's web browsing habits.

- [Github repo example supercookie](https://github.com/jonasstrehle/supercookie)
- [Paper by Scientists at University of Illinois, Chicago](https://www.cs.uic.edu/~polakis/papers/solomos-ndss21.pdf)
- [Article published in 2021 at Heise Online](https://heise.de/-5027814)
  ([English translation](https://www-heise-de.translate.goog/news/Browser-Fingerprinting-Favicons-als-Super-Cookies-5027814.html?_x_tr_sl=de&_x_tr_tl=en&_x_tr_hl=en))

It is important to note that favicon can potentially be exploited in this way.

### Screenshots

<p><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/home-page.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/home-page.png" alt="home page" width="650"/>
  </a>
</p>
<p align="center"><i>home page</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/bookmark-stats.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/bookmark-stats.png" alt="bookmark stats" width="650"/>
  </a>
</p>
<p align="center"><i>bookmark stats</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.8/bukuserver/bookmark-page-with-favicon-enabled.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.8/bukuserver/bookmark-page-with-favicon-enabled.png"
          alt="bookmark page with favicon enabled" width="650"/>
  </a>
</p>
<p align="center"><i>bookmark page <a href="#configuration">with favicon enabled</a></i></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.8a/bukuserver/bookmark-page-with-slate-theme-and-favicon-enabled.png">
    <img src="https://github.com/Buku-dev/docs/blob/v4.8a/bukuserver/bookmark-page-with-slate-theme-and-favicon-enabled.png"
         alt="bookmark page with 'slate' theme and favicon enabled" width="650"/>
  </a>
</p>
<p align="center"><i>bookmark page with 'slate' theme and favicon enabled</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/create-bookmark.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/create-bookmark.png" alt="create bookmark" width="650"/>
  </a>
</p>
<p align="center"><i>create bookmark</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/edit-bookmark.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/edit-bookmark.png" alt="edit bookmark" width="650"/>
  </a>
</p>
<p align="center"><i>edit bookmark</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/view-bookmark-details.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/view-bookmark-details.png" alt="view bookmark details" width="650"/>
  </a>
</p>
<p align="center"><i>view bookmark details</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/tag-page.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.7/bukuserver/tag-page.png" alt="tag page" width="650"/>
  </a>
</p>
<p align="center"><i>tag page</i></a></p>
