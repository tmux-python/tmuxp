WATCH_FILES= find . -type f -not -path '*/\.*' | grep -i '.*[.]py$$' 2> /dev/null


.if exists(/usr/bin/entr)
ENTR=/usr/bin/entr
.elif exists(/usr/local/bin/entr)
ENTR=/usr/local/bin/entr
.endif


test:
	py.test

entr_warn:
	@echo "----------------------------------------------------------"
	@echo "     ! File watching functionality non-operational !      "
	@echo ""
	@echo "Install entr(1) to automatically run tasks on file change."
	@echo "See http://entrproject.org/"
	@echo "----------------------------------------------------------"


watch_test:
.if defined(ENTR)
	${WATCH_FILES} | ${ENTR} -c make test
.else
	$(MAKE) entr_warn
	$(MAKE) test
	$(MAKE) entr_warn
.endif


build_docs:
	cd doc && $(MAKE) html

watch_docs:
	cd doc && $(MAKE) watch_docs

flake8:
	flake8 tmuxp tests

watch_flake8:
.if defined(ENTR)
	${WATCH_FILES} | ${ENTR} -c $(MAKE) flake8
.else
	$(MAKE) entr_warn
	$(MAKE) flake8
	$(MAKE) entr_warn
.endif
