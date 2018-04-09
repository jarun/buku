#### Install server
You need to have some packages before you install `bukuserver` on your server. So be sure to have `python3`, `python3-pip` , `python3-dev`, `libffi-dev` packages from your distribution.
##### Installing PIP, virtualenv and dependencies
```
$ python3 -m pip install --user --upgrade pip
$ python3 -m pip install --user virtualenv
$ python3 -m virtualenv env
$ source env/bin/activate
$ pip install appdirs
$ pip install beautifulsoup4
$ pip install buku
$ pip install requests
$ pip install cffi
$ pip install click
$ pip install Flask
$ pip install Flask-API
$ pip install idna
$ pip install packaging
$ pip install pyasn1
$ pip install pycparser
$ pip install six
$ pip install urllib3
```
#### Installing buku and bukuserver from PIP
```
$ pip install -e .
$ pip install -e .[server]
```

#### Webserver options

Your bookmark on buku can be accesed through browser. To run the server on host 0.0.0.1  on port 5001, run following command:

      $ bukuserver run --host 0.0.0.1 --port 5001

See more option on `bukuserver run --help` and `bukuserver --help`


#### CAUTION

This snapshot of web APIs is indicative. The program APIs are bound to change and if you need these, you may have to adapt the APIs to the current signature/return type etc. We are NOT actively updating these whenever an API changes in the main program.

