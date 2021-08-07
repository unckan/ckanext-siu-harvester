#!/bin/bash
set -euo pipefail

pip install pytest-ckan
pip install setuptools-rust

git clone https://github.com/ckan/ckanext-harvest
cd ckanext-harvest
pip install -r pip-requirements.txt
python3 setup.py develop
