#!/bin/bash
#

set -e

rm -fr dist/ build/
python3 setup.py sdist bdist_wheel

export TWINE_REPOSITORY_URL=https://upload.pypi.org/legacy/
export TWINE_USERNAME=chenpeijie
export TWINE_PASSWORD=

exec twine upload dist/*
