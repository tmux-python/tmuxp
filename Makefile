PY_FILES= find . -type f -not -path '*/\.*' | grep -i '.*[.]py$$' 2> /dev/null

entr_warn: @echo "----------------------------------------------------------"
	@echo "     ! File watching functionality non-operational !      "
	@echo "                                                          "
	@echo "Install entr(1) to automatically run tasks on file change."
	@echo "See http://entrproject.org/                               "
	@echo "----------------------------------------------------------"

isort:
	isort `${PY_FILES}`

black:
	black `${PY_FILES}` --skip-string-normalization

test:
	py.test $(test)

watch_test:
	if command -v entr > /dev/null; then ${PY_FILES} | entr -c $(MAKE) test; else $(MAKE) test entr_warn; fi

build_docs:
	cd doc && $(MAKE) html

watch_docs:
	cd doc && $(MAKE) watch_docs

flake8:
	flake8 tmuxp tests

watch_flake8:
	if command -v entr > /dev/null; then ${PY_FILES} | entr -c $(MAKE) flake8; else $(MAKE) flake8 entr_warn; fi

sync_pipfile:
	pipenv install --skip-lock --dev -r requirements/doc.txt && \
	pipenv install --skip-lock --dev -r requirements/dev.txt && \
	pipenv install --skip-lock --dev -r requirements/test.txt && \
	pipenv install --skip-lock --dev -e . && \
	pipenv install --skip-lock -r requirements/base.txt
