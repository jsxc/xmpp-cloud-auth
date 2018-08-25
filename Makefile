RELEASE		= nightly
MINOR		= 1
MODULE		= xcauth
LIBNAME		= xclib
CUSER		= ${MODULE}
PREFIX		= /usr
SBINDIR		= ${PREFIX}/sbin
LIBDIR		= ${PREFIX}/lib/python3/dist-packages/${LIBNAME}
DOCDIR		= ${PREFIX}/share/doc/${MODULE}
DATAPREFIX	= /var
LOGDIR		= ${DATAPREFIX}/log/${MODULE}
DBDIR		= ${DATAPREFIX}/lib/${MODULE}
ETCDIR		= /etc
LRTDIR		= ${ETCDIR}/logrotate.d
SDSDIR		= ${ETCDIR}/systemd/system
SU_DIR		= ${ETCDIR}/sudoers.d
DESTDIR		=

# Automatic
VERSION		= $(shell git describe | sed 's/^v//')

########################################################
# Compiling
########################################################
all:
	@echo 'INFO: Nothing to build. Continue with "make test" or "make install".'

########################################################
# Testing
########################################################
test testing:	tests
tests:		nosetests perltests loggingtests signaltests
moretests:	tests perltests-all

nosetests:
	@if [ ! -r /etc/xcauth.accounts ]; then \
	  echo 'INFO: Read tests/Coverage.md for more thorough tests'; \
	fi
	nosetests3

perltests:	perltests-direct perltests-subprocess perltests-socket1366x
perltests-all:	perltests perltests-socket2366x

perltests-direct:
	tests/run-online.pl
perltests-subprocess:
	for i in run-online-*.pl; do \
	  echo ""; \
	  echo ===============================; \
	  echo == $$i; \
	  tests/$$i subprocess || exit 1; \
	done
perltests-socket1366x:
	for i in run-online-*.pl; do \
	  echo ""; \
	  echo ===============================; \
	  echo == $$i; \
	  tests/$$i socket1366x || exit 1; \
	done
perltests-socket2366x:
	for i in run-online-*.pl; do \
	  echo ""; \
	  echo ===============================; \
	  echo == $$i; \
	  tests/$$i socket2366x || exit 1; \
	done

loggingtests:
	@echo ""; echo "### Expect warnings, but no aborts"
	# Permission denied
	echo isuser:john.doe:example.org | ./xcauth.py -t generic -l /etc
	# No such file or directory
	echo isuser:john.doe:example.org | ./xcauth.py -t generic -l /no/such/file/or/directory

signaltests:
	tests/run-signal-tests.sh

########################################################
# Installation
########################################################
install:	install_users
	${MAKE} install_dirs install_files compile_python

debinstall:	install_dirs install_files

install_users:
	if ! groups xcauth > /dev/null 2>&1; then \
	  adduser --system --group --home ${DBDIR} --gecos "XMPP Cloud Authentication" ${CUSER}; \
	fi
	# User exists, but not group of xcauth -> add group
	if [ `groups prosody 2> /dev/null | grep -v xcauth | wc -l` -gt 0 ]; then \
	  adduser prosody xcauth; \
	fi
	if [ `groups ejabberd 2> /dev/null | grep -v xcauth | wc -l` -gt 0 ]; then \
	  adduser ejabberd xcauth; \
	fi

install_dirs:
	mkdir -p ${DESTDIR}${SBINDIR} ${DESTDIR}${LIBDIR}
	mkdir -p ${DESTDIR}${ETCDIR} ${DESTDIR}${LRTDIR}
	mkdir -p ${DESTDIR}${DOCDIR} ${DESTDIR}${SDSDIR}
	mkdir -p ${DESTDIR}${LOGDIR} ${DESTDIR}${DBDIR}
	mkdir -p ${DESTDIR}${SU_DIR}
	chmod 750 ${DESTDIR}${LOGDIR} ${DESTDIR}${DBDIR}
	if group ${CUSER} > /dev/null 2>&1; then \
	  chown ${CUSER}:${CUSER} ${DESTDIR}${LOGDIR} ${DESTDIR}${DBDIR}; \
	fi

install_files:	install_dirs
	install -C -m 755 -T xcauth.py ${DESTDIR}${SBINDIR}/${MODULE}
	install -C -m 755 -T tools/xcrestart.sh ${DESTDIR}${SBINDIR}/xcrestart
	install -C -m 755 -T tools/xcejabberdctl.sh ${DESTDIR}${SBINDIR}/xcejabberdctl
	install -C -m 440 -T tools/xcauth.sudo ${DESTDIR}${SU_DIR}/xcauth
	install -C -m 644 -T tools/xcauth.logrotate ${DESTDIR}${LRTDIR}/${MODULE}
	install -C -m 644 -t ${DESTDIR}${LIBDIR} xclib/*.py
	install -C -m 644 -t ${DESTDIR}${DOCDIR} *.md LICENSE
	install -C -m 644 -t ${DESTDIR}${DOCDIR} doc/*.md doc/SystemDiagram.svg
	install -C -m 644 -t ${DESTDIR}${DOCDIR} prosody-modules/*
	if group ${CUSER} > /dev/null 2>&1; then \
	  install -C -m 640 -o ${CUSER} -g ${CUSER} xcauth.conf ${DESTDIR}${ETCDIR}; \
	else \
	  install -C -m 640 xcauth.conf ${DESTDIR}${ETCDIR}; \
	fi
	install -C -m 644 -t ${DESTDIR}${SDSDIR} systemd/*.service systemd/*.socket

compile_python:	install_files
	python3 -m compileall ${DESTDIR}${LIBDIR}

########################################################
# Packaging
########################################################
package:	deb tar sdeb
update_version:
	(echo "xcauth (${VERSION}-${MINOR}) ${RELEASE}; urgency=medium"; tail +2 debian/changelog) \
	  > debian/changelog+ \
	  && mv debian/changelog+ debian/changelog
deb:	update_version
	dpkg-buildpackage -us -uc -b
nightly:deb
	reprepro -b ../dl.jsxc.org includedeb nightly ../xcauth_${VERSION}-0~18.040_all.deb
nightly-push: nightly
	(cd ../dl.jsxc.org && git add pool/*/*/*/* && git commit -a -m "Nightly" && git push)
stable:deb
	reprepro -b ../dl.jsxc.org includedeb stable ../xcauth_${VERSION}-0~18.040_all.deb
stable-push: stable
	(cd ../dl.jsxc.org && git add pool/*/*/*/* && git commit -a -m "Stable" && git push)

tar:
	tar cfa ../xcauth_${VERSION}.orig.tar.gz \
	  --owner=${USER} --group=${USER} --mode=ugo+rX,u+w,go-w \
	  --exclude-backups --exclude-vcs --exclude-vcs-ignores \
	  --transform='s,^[.],xcauth_${VERSION}.orig,' --sort=name .

sdeb:	tar update_version
	debuild -S -i'(^[.]git|^[.]|/[.]|/__pycache__)'

########################################################
# Cleanup
########################################################
clean:
	${RM} xcauth_*.tar.gz
	${RM} -r xclib/__pycache__ xclib/tests/__pycache__
	${RM} -r debian/xcauth
	${RM} -r debian/.debhelper

.PHONY: all install test testing clean package tar deb sdeb
.PHONY: tests moretests nosetests perltests perltests-all perltests-direct
.PHONY:	perltests-subprocess perltests-socket1366x perltests-socket2366x
.PHONY:	loggingtests huptests install_dirs install_files install_users
.PHONY: compile_python
