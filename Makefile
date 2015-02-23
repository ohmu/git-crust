PYTHON_FILES = *.py

default:

tests: pylint pep8

pylint:
	python -m pylint.lint --rcfile .pylintrc $(PYTHON_FILES)

pep8:
	python -m pep8 --ignore=E501,E123 $(PYTHON_FILES)
