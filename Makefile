.PHONY: all test apidoc

python=python3

all:
	export PYTHONPATH=$(PWD); cd example; $(python) run.py

docs:
	sphinx-apidoc --separate -o docs/src/ . $(PWD)/setup.py; cd docs; \
		make clean; make html

test:
	$(python) -m unittest discover -s test

cov:
	coverage run -m unittest discover -s test
	coverage report --include=kutana/*
	coverage html

lint:
	pylint --variable-rgx='[a-z_][a-z0-9_]{0,30}$$' --max-args=8 \
		--max-attributes=12 kutana/
