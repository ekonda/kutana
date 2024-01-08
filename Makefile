.PHONY: run
run:
	poetry run -- watchmedo auto-restart \
	    --directory example/ \
	    --directory kutana/ \
	    --ignore-directories \
	    --recursive \
	    --ignore-patterns '*.pyc;*.sqlite3;*.sqlite3-journal' \
	    -- \
	    python3 -m kutana run example/config.yml

.PHONY: test
test:
	poetry run pytest ./tests

.PHONY: lint
lint:
	poetry run ruff check kutana/ tests/ && \
	poetry run ruff format --check kutana/ tests/

.PHONY: fix
fix:
	poetry run ruff check --fix kutana/ tests/ && \
	poetry run ruff format kutana/ tests/
