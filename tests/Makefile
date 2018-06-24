all:	nosetests perltests

nosetests:
	(cd .. && nosetests3)

perltests: perltests-direct perltests-subprocess perltests-socket

perltests-direct:
	cd .. && tests/run-online.pl
perltests-subprocess:
	for i in run-online-*.pl; do (cd .. && tests/$$i subprocess) || exit 1; done
perltests-socket:
	for i in run-online-*.pl; do (cd .. && tests/$$i socket) || exit 1; sleep 1; done
