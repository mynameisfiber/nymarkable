#!/bin/bash

set -o pipefail -u -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BUILD_DIR=${HOME}/.nymarkable/build/

source ${SCRIPT_DIR}/venv/bin/activate
if [ -e ${SCRIPT_DIR}/env ] ; then
    source ${SCRIPT_DIR}/env
fi

function list-files() {
    directory=$1
    filter=$2
    rmapi ls "${directory}" | grep -oP "\[f\]\s*\K(.*)$" | grep "${filter}"
}


DATE=$( date +"%Y-%m-%d" )
cur_basename="${DATE}_nytimes"
cur_filename="${cur_basename}.pdf"
cur_abspath="${BUILD_DIR}/${cur_filename}"

echo "Edition filename: $cur_basename"
if list-files /Reading/nytimes/ "${cur_basename}"; then
    echo "Current edition already exists on device"
    exit
fi

mkdir -p "${BUILD_DIR}" || true
find "${BUILD_DIR}" -type f -delete || true

nymarkable \
    create-edition \
        --section "The Front Page" \
        --section "International" \
        --section "National" \
        --section "Editorials, Op-Ed and Letters" \
        --section "The Arts" \
        "${cur_abspath}"

echo "Creating directory"
rmapi mkdir /Reading/nytimes || true

echo "Uploading"
rmapi put "${cur_abspath}" /Reading/nytimes/

echo "Clearing all but most recent 12 editions"
list-files /Reading/nytimes/ "nytimes" | sort -rn | head -n -12 | (
    while read FNAME; do
        echo "Deleting old edition: ${FNAME}";
        rmapi rm "${FNAME}";
    done
)
