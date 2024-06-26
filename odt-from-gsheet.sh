#!/usr/bin/env bash
# gsheet->json->odt pipeline

# parameters
DOCUMENT=$1

# set echo off
PYTHON=python3

# run the libre office headless server
soffice --headless --invisible --accept="socket,host=localhost,port=8100;urp;" &
sleep 2

# json-from-gsheet
pushd ./gsheet-to-json/src
${PYTHON} json-from-gsheet.py --config "../conf/config.yml" --gsheet ${DOCUMENT}

if [ ${?} -ne 0 ]; then
  popd && exit 1
else
  popd
fi

# odt-from-json
pushd ./json-to-odt/src
${PYTHON} odt-from-json.py --config "../conf/config.yml" --json ${DOCUMENT}

if [ ${?} -ne 0 ]; then
  popd && exit 1
else
  popd
fi
