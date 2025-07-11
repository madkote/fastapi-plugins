#!make
.PHONY: clean-pyc clean-build
.DEFAULT_GOAL := help

SHELL = /bin/bash
PYPACKAGE = fastapi_plugins

help:
	@echo ""
	@echo " +---------------------------------------+"
	@echo " | ${PYPACKAGE}                       |"
	@echo " +---------------------------------------+"
	@echo "    clean"
	@echo "        Remove python and build artifacts"
	@echo "    install"
	@echo "        Install requirements for development and testing"
	@echo "    demo"
	@echo "        Run a simple demo"
	@echo ""
	@echo "    test"
	@echo "        Run unit tests"
	@echo "    test-all"
	@echo "        Run integration tests"
	@echo ""

clean-pyc:
	@echo $@
	find ./${PYPACKAGE} -name '*.pyc' -exec rm --force {} +
	find ./${PYPACKAGE} -name '*.pyo' -exec rm --force {} +
	find ./${PYPACKAGE} -name '*~'    -exec rm --force {} +

clean-build:
	@echo $@
	rm --force --recursive .tox/
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info
	rm --force --recursive .pytest_cache/

clean-docker:
	@echo $@
	docker container prune -f

clean-pycache:
	@echo $@
	find . -name '__pycache__' -exec rm -rf {} +

clean: clean-build clean-docker clean-pyc clean-pycache

install: clean
	@echo $@
	pip install --no-cache-dir -U build pip setuptools twine wheel
	pip install --no-cache-dir -U --force-reinstall -r requirements.txt
	rm -rf build *.egg-info
	pip uninstall ${PYPACKAGE} -y || true

demo: clean
	@echo $@
	python demo.py

demo-app: clean
	@echo $@
	uvicorn scripts.demo_app:app

lint: clean
	@echo $@
	pdm run lint

test-pdm:
	@echo $@
	pdm run test

test-unit: clean docker-up-test test-pdm docker-down-test
	@echo $@

test-toxtox:
	@echo $@
	tox -vv

test-tox: clean docker-up-test test-toxtox docker-down-test
	@echo $@

test: test-unit
	@echo $@

test-all: clean docker-up-test test-pdm test-toxtox docker-down-test
	@echo $@

pypi-build-twine:
	twine check dist/*

pypi-build-wheel:
	pdm run build

pypi-build: clean test-all pypi-build-wheel pypi-build-twine
	@echo $@

pypi-upload-test:
	@echo $@
	python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

pypi-upload:
	@echo $@
	python -m twine upload dist/*

docker-build-dev:
	@echo $@
	docker compose -f docker-compose.memcached.yml -f docker-compose.sentinel.yml build

docker-up: clean-docker
	@echo $@
	docker compose build --force-rm --no-cache --pull && docker compose -f docker-compose.yml -f docker-compose.redis.yml -f docker-compose.memcached.yml up --build

docker-up-dev: clean-docker docker-build-dev
	@echo $@
	docker compose -f docker-compose.memcached.yml -f docker-compose.sentinel.yml up

docker-up-test: clean-docker docker-build-dev
	@echo $@
	docker compose -f docker-compose.memcached.yml -f docker-compose.sentinel.yml up -d
	sleep 5
	docker ps

docker-down-test:
	@echo $@
	docker compose -f docker-compose.memcached.yml -f docker-compose.sentinel.yml down
