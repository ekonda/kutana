.PHONY: all test apidoc

python=python3

all:
	export PYTHONPATH=$(PWD); cd example; $(python) run.py

apidoc:
	sphinx-apidoc --separate -o docs/src/ . $(PWD)/setup.py

test:
	$(python) -m unittest discover -s test

cov:
	coverage run -m unittest discover -s test
	coverage report --include=kutana/*

lint:
	pylint --variable-rgx='[a-z_][a-z0-9_]{0,30}$$' kutana/
