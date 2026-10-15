.PHONY: check test run migrate

check:
	python manage.py check

test:
	python -m pytest -q

run:
	python manage.py runserver

migrate:
	python manage.py migrate
