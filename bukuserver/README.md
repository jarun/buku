#### Install server

You need to have some packages before you install `bukuserver` on your server. So be sure to have `python3`, `python3-pip` , `python3-dev`, `libffi-dev` packages from your distribution.

##### Installing PIP, virtualenv and dependencies

```
$ python3 -m pip install --user --upgrade pip
$ python3 -m pip install --user virtualenv
$ python3 -m virtualenv env
$ source env/bin/activate
$ git clone https://github.com/jarun/Buku
$ cd Buku
$ pip3 install .[server]
```

#### Installing buku and bukuserver from PIP

```
$ pip3 install buku[server]
```

#### Webserver options

To run the server on host 127.0.0.1, port 5001, run following command:

      $ bukuserver run --host 127.0.0.1 --port 5001
Visit `127.0.0.1:5001` in your browser to access your bookmarks.

See more option on `bukuserver run --help` and `bukuserver --help`

#### CAUTION

This snapshot of web APIs is indicative. The program APIs are bound to change and if you need these, you may have to adapt the APIs to the current signature/return type etc. We are NOT actively updating these whenever an API changes in the main program.
