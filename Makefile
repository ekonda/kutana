.PHONY: all test docs

all: run

install:
	python3 -m pip install .

run:
	watchmedo auto-restart \
		--directory example/ \
		--directory kutana/ \
		--ignore-directories \
		--recursive \
		--ignore-patterns '*.pyc;*.sqlite3;*.sqlite3-journal' \
		-- \
		python3 -m kutana run example/config.yml

test:
	python3 -m coverage run -m --include=kutana/* pytest -vv tests/
	python3 -m coverage report -m --fail-under=70

lint:
	python3 -m flake8 kutana/ --count --max-complexity=10 --ignore=E203 --max-line-length=127 --statistics
