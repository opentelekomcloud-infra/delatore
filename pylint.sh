#!/usr/bin/env bash

pylint delatore
ex_code=$?

# pylint exit codes:
# 0 no error
# 1 fatal message issued
# 2 error message issued
# 4 warning message issued
# 8 refactor message issued
# 16 convention message issued

echo pylint exit code is ${ex_code}

if (( ${ex_code} > 0 )) && (( ${ex_code} < 8 )); then  # warning+
    exit 1
fi
