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
in this directory. Some of the tests will only run, if
`/etc/xcauth.conf` exists. They will assume that
it points to a server accounts with the following
username/password pairs:

| Username        | Password |
| --------------- | -------- |
| testbed         | chilobig |
| test@example.ch | nigorami |

Please disable these accounts whenever you are not
using them for tests, as someone might abuse them.
