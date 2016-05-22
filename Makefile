test:
	py.test

watch_test:
	if command -v entr > /dev/null; then find . -type f -not -path '*/\.*' | grep -i '.*[.]py' | entr -c make test; else make test; echo "\nInstall entr(1) to automatically run tests on file change.\n See http://entrproject.org/"; fi

nose:
	nosetests tmuxp/testsuite/*.py -m "^test*."

nose_time:
	nosetests tmuxp/testsuite/*.py -m "^test*." --with-timer --timer-top-n 15

build_docs:
	cd doc && $(MAKE) html

watch_docs:
	cd doc && $(MAKE) watch_docs

flake8:
	flake8 tmuxp tests

watch_flake8:
	if command -v entr > /dev/null; then find . -type f -not -path '*/\.*' | grep -i '.*[.][py]' | entr -c make flake8; else make flake8; echo "\nInstall entr(1) to automatically run tests on file change.\n See http://entrproject.org/"; fi

.PHONY: flake8
