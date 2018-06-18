all:	nosetests perltests

nosetests:
	(cd .. && nosetests3)

perltests:
	for i in run-online*.pl; do (cd .. && tests/$$i) || exit 1; done
