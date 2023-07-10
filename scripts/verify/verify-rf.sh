#!/bin/bash
set -euo pipefail

ROOTDIR=$(git rev-parse --show-toplevel)

RF_VENV="${ROOTDIR}/_output/robotenv"
"${ROOTDIR}/scripts/fetch_tools.sh" robotframework

cd "${ROOTDIR}/test"

set -x
"${RF_VENV}/bin/robocop" --exclude 1015

"${RF_VENV}/bin/robotidy" --check --diff .
