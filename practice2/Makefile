.PHONY: test demo

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

demo:
	sh run.sh examples/a.csv
	sh run.sh examples/b.csv
	sh run.sh examples/cycle.csv
