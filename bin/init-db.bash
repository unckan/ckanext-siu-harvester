#!/bin/bash
set -euo pipefail

ckan -c ./test.ini db init
