# ejabberd-cloud-auth

:warning: work in progress. Don't use this!

```
sudo apt-get install python python-pip
sudo -u ejabberd -H pip install requests

vim /etc/ejabberd/ejabberd.yml

auth_method: external
extauth_program: "/opt/ejabberd-cloud-auth/external_cloud.py"
```

https://www.ejabberd.im/files/doc/dev.html#htoc9
