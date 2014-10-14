all: pylint test

pylint:
	flake8 -v .
test:
	nosetests --with-coverage --cover-package=sanji --cover-erase

.PHONY: pylint test
