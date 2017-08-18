# Testing

For testing, we use `nose`. This probably can be installed using
```sh
apt install python-nose
```
or
```sh
pip install nose
```
on your system. To run the tests, type
```sh
nosetests
```
or (if you also want coverage information),
```sh
nosetests --with-coverage --cover-package=xclib
```
in this directory. Some of the tests will only run,
if `/etc/xcauth.accounts` exists. Then, it will read
tab-separated username/password pairs from that file
and use the settings in `/etc/xcauth.conf` to verify
those passwords. Additionally, it will assume that
a user `nosuchuser` **does not exist**. Please make
sure that only authorized users can read these
configuration files.
