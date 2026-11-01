.PHONY: check lint test

check: lint test

lint:
	python -m ruff check apps/api/app apps/api/tests
	npm --prefix apps/web run lint

test:
	python -m pytest apps/api/tests
