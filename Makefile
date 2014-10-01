all: pylint test

pylint:
	flake8 -v .
test:
	nosetests --with-coverage --cover-package=sanji

.PHONY: pylint test
