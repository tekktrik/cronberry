# SPDX-FileCopyrightText: 2024 Alec Delaney
# SPDX-License-Identifier: GPL-3.0-or-later

.PHONY: lint
lint:
	pre-commit run ruff --all-files

.PHONY: format
format:
	pre-commit run ruff-format --all-files

.PHONY: reuse
reuse:
	pre-commit run reuse --all-files

.PHONY: check
check:
	pre-commit run --all-files

.PHONY: test
test:
	coverage run -m pytest
	coverage report
	coverage html

.PHONY: docs
docs:
	pip install -r docs/requirements.txt
	sphinx-build -E -W -b html docs docs/build/html

.PHONY: install
install:
	mv VERSION COPY_VERSION
	echo "0.0.0" > VERSION
	pip install -e .[dev]
	mv COPY_VERSION VERSION

.PHONY: uninstall
uninstall:
	pip uninstall -y cronberry

prepare: check test docs
