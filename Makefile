test:
	py.test

entr_warn:
	echo "\nInstall entr(1) to automatically run tasks on file change.\n See http://entrproject.org/"

watch_test:
	if command -v entr > /dev/null; then find . -type f -not -path '*/\.*' | grep -i '.*[.]py' | entr -c make test; else make test warn; fi

build_docs:
	cd doc && $(MAKE) html

watch_docs:
	cd doc && $(MAKE) watch_docs

flake8:
	flake8 tmuxp tests

watch_flake8:
	if command -v entr > /dev/null; then find . -type f -not -path '*/\.*' | grep -i '.*[.][py]' | entr -c make flake8; else make flake8 warn; fi

.PHONY: flake8
