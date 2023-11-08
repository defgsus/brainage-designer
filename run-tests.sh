#!/bin/bash

export PYTHONPATH=.
export BAD_DATABASE_NAME=brainage-dev-test

python -m unittest discover "$@"


