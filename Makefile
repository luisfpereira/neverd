doc:
	rm -r docs/_build
	cd docs && make html

test:
	pytest --cov=neverd 

lint:
	pylint src/neverd

wheel:
	rm -rf build
	rm -rf dist
	python setup.py sdist bdist_wheel

upload_test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

upload:
	twine upload dist/*
