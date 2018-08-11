MODULE		= xcauth
LIBNAME		= xclib
USER		= ${MODULE}
PREFIX		= /usr
BINDIR		= ${PREFIX}/bin
LIBDIR		= ${PREFIX}/lib/python3/dist-packages/${LIBNAME}
DOCDIR		= ${PREFIX}/share/doc/${MODULE}
DATAPREFIX	= /var
LOGDIR		= ${DATAPREFIX}/log/${MODULE}
DBDIR		= ${DATAPREFIX}/lib/${MODULE}
ETCDIR		= /etc
LRTDIR		= ${ETCDIR}/logrotate.d

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
install:
		adduser --system --group --home ${DBDIR} --gecos "XMPP Cloud Authentication" ${USER}
		groups prosody > /dev/null 2>&1 && adduser prosody xcauth
		groups ejabberd > /dev/null 2>&1 && adduser ejabberd xcauth
		mkdir -p ${BINDIR} ${LIBDIR} ${LOGDIR} ${DBDIR}
		chmod 770 ${LOGDIR} ${DBDIR}
		chmod ${USER}:${USER} ${LOGDIR} ${DBDIR}
		install -C -m 755 -T xcauth.py ${BINDIR}/${MODULE}
		install -C -m 755 -T tools/xcrestart.sh ${BINDIR}/xcrestart
		install -C -m 644 -T tools/xcauth.logrotate ${LRTDIR}/${MODULE}
		install -C -m 644 -t ${LIBDIR} xclib/*.py
		install -C -m 644 -t ${DOCDIR} *.md LICENSE
		install -C -m 644 -t ${DOCDIR} doc/*.md doc/SystemDiagram.svg
		install -C -m 640 -T -o ${USER} -g ${USER} xcauth.conf ${ETCDIR}


.PHONY: all install test testing
.PHONY: tests moretests nosetests perltests perltests-all perltests-direct
.PHONY:	perltests-subprocess perltests-socket1366x perltests-socket2366x
.PHONY:	loggingtests huptests
