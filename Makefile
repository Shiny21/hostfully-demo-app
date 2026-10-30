.PHONY: install run test coverage lint docker-up docker-down clean

PYTHON ?= python3
PYTEST ?= pytest

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

run:
	FLASK_APP=app:create_app FLASK_DEBUG=1 flask run --host=0.0.0.0 --port=5000

test:
	$(PYTEST) -v

coverage:
	$(PYTEST) --cov=app --cov-report=term-missing

lint:
	ruff check app tests

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

clean:
	rm -rf .pytest_cache .coverage htmlcov __pycache__
