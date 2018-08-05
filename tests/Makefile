all:	nosetests perltests loggingtests
more:	really-all
really-all:	nosetests perltests-all

nosetests:
	(cd .. && nosetests3)

perltests: perltests-direct perltests-subprocess perltests-socket1366x
perltests-all: perltests perltests-socket2366x

perltests-direct:
	cd .. && tests/run-online.pl
perltests-subprocess:
	for i in run-online-*.pl; do echo ""; echo ===============================; echo == $$i; (cd .. && tests/$$i subprocess) || exit 1; done
perltests-socket1366x:
	for i in run-online-*.pl; do echo ""; echo ===============================; echo == $$i; (cd .. && tests/$$i socket1366x) || exit 1; sleep 1; done
perltests-socket2366x:
	for i in run-online-*.pl; do echo ""; echo ===============================; echo == $$i; (cd .. && tests/$$i socket2366x) || exit 1; done

loggingtests:
	@echo ""; echo "### Expect warnings, but no aborts"
# Permission denied
	echo isuser:john.doe:example.org | ../xcauth.py -t generic -l /etc
# No such file or directory
	echo isuser:john.doe:example.org | ../xcauth.py -t generic -l /no/such/file/or/directory
