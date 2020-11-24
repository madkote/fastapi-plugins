#!make
.PHONY: clean-pyc clean-build
.DEFAULT_GOAL := help

SHELL = /bin/bash

help:
	@echo ""
	@echo " +---------------------------------------+"
	@echo " | FastAPI Plugins                       |"
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
	find . -name '*.pyc' -exec rm --force {} +
	find . -name '*.pyo' -exec rm --force {} +
	find . -name '*~'    -exec rm --force {} +

clean-build:
	@echo $@
	rm --force --recursive .tox/
	rm --force --recursive build/
	rm --force --recursive dist/
	rm --force --recursive *.egg-info
	rm --force --recursive .pytest_cache/

clean-pycache:
	@echo $@
	find . -name '__pycache__' -exec rm -rf {} +

clean: clean-build clean-pyc clean-pycache

install: clean
	@echo $@
	pip install --no-cache-dir -U -r requirements.txt

demo: clean
	@echo $@
	python demo.py

demo-app: clean
	@echo $@
	uvicorn scripts/demo_app:app

flake: clean
	@echo $@
	flake8 --statistics --ignore E252 fastapi_plugins tests scripts

bandit: clean
	@echo $@
	bandit -r fastapi_plugins/ tests/ scripts/ demo.py

test-unit: clean flake bandit
	@echo $@
	time python -m pytest -v -x tests/ --cov=fastapi_plugins

test-tox: clean
	@echo $@
	tox -vv

test: test-unit
	@echo $@

test-all: test-unit test-tox
	@echo $@

#md2rst:
#	@echo $@
#	m2r _README.md
#	mv -f _README.rst README.rst

pypi-deps:
	@echo $@
	pip install -U twine

pypi-build: clean test-all pypi-deps
	@echo $@
	python setup.py sdist bdist_wheel
	twine check dist/*

pypi-upload-test: pypi-deps
	@echo $@
	python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

pypi-upload: pypi-deps
	@echo $@
	python -m twine upload dist/*

docker-up:
	@echo $@
	docker container prune -f && docker-compose up --build

docker-up-redis:
	@echo $@
	docker container prune -f && docker-compose -f _docker/docker-compose.yml up --build
