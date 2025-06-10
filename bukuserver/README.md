## Bukuserver

_**Note: see [the runner script](https://github.com/jarun/buku/wiki/Bukuserver-%28WebUI%29#runner-script) for advanced installation/running/DB swapping functionality**_

### Table of Contents

- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [From PyPi](#from-pypi)
  - [From source](#from-source)
  - [Using Docker](#using-docker)
  - [Using Docker Compose](#using-docker-compose)
- [Webserver options](#webserver-options)
- [Configuration](#configuration)
- [API](#api)
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

The following are [os env config variables](#how-to-specify-environment-variables) available for bukuserver.

_**Important:** all of them have a shared prefix_ **`BUKUSERVER_`**.

| Name (_without prefix_) | Description | Value _²_ |
| --- | --- | --- |
| PER_PAGE | bookmarks per page | positive integer [default: 10] |
| SECRET_KEY | [flask secret key](https://flask.palletsprojects.com/config/#SECRET_KEY) | string [default: random value] |
| URL_RENDER_MODE | url render mode | `full`, `netloc` or `netloc-tag` [default: `full`] |
| DB_FILE | full path to db file<em>³</em> | path string [default: standard path for buku] |
| READONLY | read-only mode | boolean<em>¹</em> [default: `false`] |
| DISABLE_FAVICON | disable bookmark [favicons](https://wikipedia.org/wiki/Favicon) | boolean<em>¹</em> [default: `true`] ([here's why](#why-favicons-are-disabled-by-default))|
| OPEN_IN_NEW_TAB | url link open in new tab | boolean<em>¹</em> [default: `false`] |
| REVERSE_PROXY_PATH | reverse proxy path<em>⁵</em> | string |
| THEME | [GUI theme](https://bootswatch.com/3) | string [default: `default`] (`slate` is a good pick for dark mode) |
| LOCALE | GUI language<em>⁴</em> (partial support) | string [default: `en`] |
| DEBUG | debug mode (verbose logging etc.) | boolean<em>¹</em> [default: `false`] |

_**¹**_ valid boolean values are `true`, `false`, `1`, `0` (case-insensitive).

_**²**_ if input is invalid, the default value will be used if defined

_**³**_ `BUKUSERVER_DB_FILE` can be a DB name (plain filename without extension; cannot contain `.`). The specified DB with `.db` extension is located in default DB directory (which you can override with `BUKU_DEFAULT_DBDIR`).

_**⁴**_ `BUKUSERVER_LOCALE` requires either `flask_babel` or `flask_babelex` installed

_**⁵**_ the value for `BUKUSERVER_REVERSE_PROXY_PATH` is recommended to include preceding slash and not have trailing slash (i.e. use `/foo` not `/foo/`)


#### How to specify environment variables

E.g. to set bukuserver to show 100 items per page run the following command:
```
# on linux
$ export BUKUSERVER_PER_PAGE=100

# on windows
$ SET BUKUSERVER_PER_PAGE=100

# in dockerfile
ENV BUKUSERVER_PER_PAGE=100

# in env file
BUKUSERVER_PER_PAGE=100
```

Note: an env file can be supplied either [by providing `--env-file` CLI argument](https://flask.palletsprojects.com/en/stable/cli/#environment-variables-from-dotenv) (requires `python-dotenv` installed),
or as config for [the runner script](https://github.com/jarun/buku/wiki/Bukuserver-%28WebUI%29#runner-script).


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

### API

Bukuserver implements a RESTful API that provides an HTTP-based interface for the main functionality.

The API root is at `/api`; you can also access a [Swagger](https://swagger.io/tools/swagger-ui)-based interactive doc at the endpoint `/apidocs` (e.g. `http://localhost:5000/apidocs`).

_**Note: unlike regular IDs, indices aren't static; they're likely to change if used with ID**_
* `/api/tags` can be used to `GET` the list of all tags
* `/api/tags/{tag}` can be used to `GET` information on specified tag, as well as `DELETE` or replace it with new tags (`PUT`) in all bookmarks
* `/api/bookmarks` can be used to `GET` or `DELETE` all bookmarks, as well as create (`POST`) a new one
* `/api/bookmarks/{index}` can be used to `GET`, `DELETE` or update (`PUT`) an existing bookmark
* `/api/bookmarks/{start_index}/{end_index}` can be used to `GET`, `DELETE` or update (`PUT`) bookmarks in existing index range
* `/api/bookmarks/search` can be used to `GET` or `DELETE` bookmarks matching the query (you can use it to obtain current index by URL)
* ~~`/api/bookmarks/{index}/tiny` can be used to `GET` a shortened URL~~ ([the service providing this functionality is no longer available](https://web.archive.org/web/20250109212915/https://tny.im/))
* `/api/bookmarks/{index}/refresh` can be used to update (`POST`) data for a bookmark by remotely fetching & parsing the URL
* `/api/bookmarks/refresh` can be used to update (`POST`) data for _**all**_ bookmarks by remotely fetching & parsing the URLs
* `/api/fetch_data` can be used to invoke (`POST`) the fetch+parse functionality for an arbitrary URL
* `/api/network_handle` can be used to invoke (`POST`) the fetch+parse functionality for an arbitrary URL (_outdated interface_)

Also note that certain `POST`/`DELETE` endpoints (bookmarks search & data fetch) expect their parameters in urlencoded format, while others expect JSON.

### Screenshots

_**Note: more screenshots (to show off `default` & `slate` themes) can be found [on the respective project wiki page](https://github.com/jarun/buku/wiki/Bukuserver-%28WebUI%29)**_

<p><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/home-page.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/home-page.png" alt="home page" width="650"/>
  </a>
</p>
<p align="center"><i>home page</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/bookmark-stats.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/bookmark-stats.png" alt="bookmark stats" width="650"/>
  </a>
</p>
<p align="center"><i>bookmark stats</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/bookmark-page-with-favicon-enabled.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/bookmark-page-with-favicon-enabled.png"
          alt="bookmark page with favicon enabled and 'netloc-tag' URL render mode" width="650"/>
  </a>
</p>
<p align="center"><i>bookmark page <a href="#configuration">with favicon enabled and 'netloc-tag' URL render mode</a></i></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/bookmark-page-with-slate-theme-and-favicon-enabled.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/bookmark-page-with-slate-theme-and-favicon-enabled.png"
         alt="bookmark page with 'slate' theme and favicon enabled" width="650"/>
  </a>
</p>
<p align="center"><i>bookmark page with 'slate' theme, favicon enabled and 'netloc-tag' URL render mode</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/create-bookmark.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/create-bookmark.png" alt="create bookmark" width="650"/>
  </a>
</p>
<p align="center"><i>create bookmark</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/edit-bookmark.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/edit-bookmark.png" alt="edit bookmark" width="650"/>
  </a>
</p>
<p align="center"><i>edit bookmark</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/view-bookmark-details.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/view-bookmark-details.png" alt="view bookmark details" width="650"/>
  </a>
</p>
<p align="center"><i>view bookmark details</i></a></p>

<p><br><br></p>
<p align="center">
  <a href="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/tag-page.png?raw=true">
    <img src="https://github.com/Buku-dev/docs/blob/v4.9-bootstrap3/bukuserver/tag-page.png" alt="tag page" width="650"/>
  </a>
</p>
<p align="center"><i>tag page</i></a></p>
