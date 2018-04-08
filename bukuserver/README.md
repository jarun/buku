#### Install server
You need to have some packages before you install `bukuserver` on your server. So be sure to have `python3`, `python3-pip` , `python3-dev`, `libffi-dev` packages from your distribution.
##### Installing PIP, virtualenv and dependencies
```
$ python3 -m pip install --user --upgrade pip
$ python3 -m pip install --user virtualenv
$ python3 -m virtualenv env
$ source env/bin/activate
(env) $ pip install appdirs
(env) $ pip install beautifulsoup4
(env) $ pip install buku
(env) $ pip install requests
(env) $ pip install cffi
(env) $ pip install click
(env) $ pip install Flask
(env) $ pip install Flask-API
(env) $ pip install idna
(env) $ pip install packaging
(env) $ pip install pyasn1
(env) $ pip install pycparser
(env) $ pip install six
(env) $ pip install urllib3
```
#### Installing buku and bukuserver from PIP
```
(env) $ pip install -e .
(env) $ pip install -e .[server]
```

#### Webserver options

Your bookmark on buku can be accesed through browser. To run the server on host 0.0.0.1  on port 5001, run following command:

      $ bukuserver run --host 0.0.0.1 --port 5001

See more option on `bukuserver run --help` and `bukuserver --help`


#### CAUTION

This snapshot of web APIs is indicative. The program APIs are bound to change and if you need these, you may have to adapt the APIs to the current signature/return type etc. We are NOT actively updating these whenever an API changes in the main program.

