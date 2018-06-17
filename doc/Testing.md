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
nosetests3
```
or (if you also want coverage information),
```sh
nosetests3 --with-coverage --cover-package=xclib
```
in this directory. Some of the tests will only run,
if `/etc/xcauth.accounts` exists. Then, it will read
tab-separated username/password pairs from that file
and use the settings in `/etc/xcauth.conf` to verify
those passwords. Additionally, it will assume that
a user `nosuchuser` **does not exist**. Please make
sure that only authorized users can read these
configuration files.

The full command-line tool can be tested when typing
```sh
tests/run-online.pl /etc/xcauth.accounts
```
in the current directory.
This will also use `/etc/xcauth.accounts`, so this
needs to exist together with your valid `/etc/xcauth.conf`.

## Format of `/etc/xcauth.accounts`
Line-based, tab-separated file with the following fields:

### Lines not starting with a tab
1. login
2. domain (typically your default domain)
3. password

### Lines starting with a tab
1. (empty, before the first tab)
2. command: isuser, auth, roster
3. expected response

### Lines starting with '#' and empty lines will be ignored

### Example file
The table column separators will be single tabs in the real file.

| Field 1   | Field 2          | Field 3                                         |
| --------- | ---------------- | ----------------------------------------------- |
| user1     | example.ch       | p4ssw0rd                                        |
|           | isuser           | True                                            |
|           | auth             | True                                            |
|           | roster           | {"result":"success","data":{"sharedRoster":[]}} |
| user1     | example.ch       | wr0ng-p4ssw05d                                  |
|           | isuser           | True                                            |
|           | auth             | False                                           |
| nosuchuser| example.ch       | dontcare                                        |
|           | isuser           | False                                           |
