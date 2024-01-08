all: run

run:
	poetry run -- watchmedo auto-restart \
		--directory example/ \
		--directory kutana/ \
		--ignore-directories \
		--recursive \
		--ignore-patterns '*.pyc;*.sqlite3;*.sqlite3-journal' \
		-- \
		python3 -m kutana run example/config.yml

test:
	poetry run pytest --asyncio-mode=auto --cov=kutana --cov-report=term-missing ./tests

lint:
	poetry run ruff check kutana/ tests/ && \
	poetry run ruff format --check kutana/ tests/

fix:
	poetry run ruff check --fix kutana/ tests/ && \
	poetry run ruff format kutana/ tests/
