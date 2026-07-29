.PHONY: run test lint format check deps build

run:
	uvicorn app.main:app --reload

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=app --cov-report=term-missing

lint:
	ruff check app tests

format:
	black app tests

check:
	mypy app

deps:
	pip install -r requirements.txt

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down
