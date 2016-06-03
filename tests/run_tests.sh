#!/bin/bash

tests_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $tests_dir
python -m pytest test_*.py
