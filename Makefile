all: pylint test

pylint:
	flake8 -v ./sanji
test:
	nosetests --with-coverage --cover-package=sanji --cover-erase
tox:
	tox

.PHONY: pylint test tox
