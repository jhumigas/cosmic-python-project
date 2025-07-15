OUTPUT_DIR= .
SRC_DIR= src/allocation

.PHONY: help
help:
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } ' $(MAKEFILE_LIST)

.PHONY: install
install: ## install dependencies
	uv sync --locked --all-extras --dev

.PHONY: check-bandit
check-bandit: ## code vulnerability security scan
	uvx bandit -c pyproject.toml -r .

# Numpy safety check error are ignored du to sktime dependencies. Turn numpy to 1.22.0 to resolve safety check when
# this issue will be resolved https://github.com/alan-turing-institute/sktime/discussions/2037
.PHONY: check-safety
check-safety: ## dependencies scan with safety
	uv pip freeze | uvx safety check -i 44715 -i 44716 -i 44717 --stdin

.PHONY: pre-commit
pre-commit: ## run pre-commit hooks
	uvx pre-commit run --all-files

.PHONY: install-pre-commit
install-pre-commit: ## install pre-commit hooks
	uvx pre-commit install

.PHONY: detect-secrets
detect-secrets: ## detect secrets in code
	uvx detect-secrets scan $(SRC_DIR) --all-files

.PHONY: format
format: ## format code
	uvx ruff format .

.PHONY: lint
lint: ## lint code
	uvx ruff check .

.PHONY: unit-test
unit-test:  ## run unit tests
	uv run pytest tests/unit

.PHONY: integration-test
integration-test:  ## run integration tests
	uv run pytest tests/integration

.PHONY: e2e-test
e2e-test:  ## run end-to-end tests
	uv run pytest tests/e2e

.PHONY: test-coverage
test-coverage: ## run unit tests with coverage and generate coverage xml and html report
	uv run pytest tests -s --cov-append --doctest-modules --junitxml=$(OUTPUT_DIR)/junit/unit-tests-results.xml --cov=$(SRC_DIR) --cov-report=xml:$(OUTPUT_DIR)/coverage.xml --cov-report=html:$(OUTPUT_DIR)/htmlcov --cov-report term

.PHONY: tests
tests: docker-down docker-build docker-up
	uv run pytest tests

.PHONY: docker-build
docker-build: ## build containers
	docker compose build

.PHONY: docker-up
docker-up: ## start containers
	docker compose up -d

.PHONY: docker-down
docker-down:  ## stop containers
	docker compose down

.PHONY: docker-logs
docker-logs: ## show logs
	docker compose logs app | tail -100

.PHONY: start-dev-flask-app
start-dev-flask-app: ## start dev mode
	FLASK_APP=src/allocation/entrypoints/flask_app.py flask run --host=0.0.0.0 --port=80

.PHONY: start-dev-fast-app
start-dev-fast-app: ## start dev mode
	uv run fastapi dev src/allocation/entrypoints/fast_app.py

.PHONY: start-dev
start-dev: docker-up start-dev-fast-app


.PHONY: stop-dev
stop-dev:
	docker compose down

.PHONY: start-dev-redis-eventconsumer
start-dev-redis-eventconsumer: ## start dev mode
	uv run python src/allocation/entrypoints/redis_eventconsumer.py