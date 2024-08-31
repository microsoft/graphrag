install:
	pip install poetry && poetry install

# setup your workspace variables
setup:
	python -m graphrag.index --init --root ./ragtest

# run the pipeline
run:
	python -m graphrag.index --root ./ragtest

# make a global query
query-global:
	python -m graphrag.query \
		--root ./ragtest \
		--method global \
		"What underlying message does the author convey about the impact of AI on human employment?"

# make a local query
query-local:
	python -m graphrag.query \
		--root ./ragtest \
		--method local \
		"What did Marcus Hale announce to the investors regarding the engineering team?"

# bonus query
query-bonus:
	python -m graphrag.query \
		--root ./ragtest \
		--method global \
		"Why did Ethan choose to mentor Luca, despite knowing his role was diminishing?"