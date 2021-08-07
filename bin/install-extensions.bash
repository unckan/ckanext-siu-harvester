#!/bin/bash
set -euo pipefail

pip install setuptools-rust

git clone https://github.com/ckan/ckanext-harvest
cd ckanext-harvest
pip install -r requirements.txt
python3 setup.py develop
