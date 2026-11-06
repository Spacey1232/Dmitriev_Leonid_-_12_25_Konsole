.PHONY: test test-shell test-graph

test: test-shell test-graph

test-shell:
	PYTHONPATH=practice1/step-1 python3 -m unittest discover -s practice1/step-1/tests -v

test-graph:
	$(MAKE) -C practice2 test
