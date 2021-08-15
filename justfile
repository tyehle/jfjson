test:
    PYTHONPATH=src python3 -m pytest

type:
    mypy src test

lint:
    flake8 src test
    black --check src test

format:
    black src test

check:
    tox

clean:
    rm -rf src/jfjson.egg-info build dist

build: clean
    python3 setup.py build sdist bdist_wheel

publish: check build
    git tag "v$(python3 setup.py --version)"
    git push --tags
    twine upload dist/*
