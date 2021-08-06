#!/bin/bash
set -euo pipefail

pip install setuptools-rust

git clone --depth 1 --branch release-2.1.0 https://github.com/ckan/ckanext-harvest
(cd ckanext-harvest && python3 setup.py develop)
