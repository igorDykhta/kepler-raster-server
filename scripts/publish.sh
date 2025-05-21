#! /usr/bin/env bash

rm -rf dist build *.egg-info
python3 -m build

python3 -m twine upload --repository testpypi dist/*

# twine upload dist/*