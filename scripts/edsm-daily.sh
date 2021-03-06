#!/bin/bash

EDSMDIR="/srv/eddata/EDSM"
SCRIPTSDIR="/srv/eddata/scripts"
BODIESDIR="/srv/eddata/namedbodies"

ENDDATE="$(date +"%Y-%m-%d+%H:%M:%S" --utc --date="now + 1 hour")"
STARTDATE="$(date +"%Y-%m-%d+00:00:00" --utc --date="yesterday")"
DATE="$(date +"%Y-%m-%d" --utc)"

export PYTHONIOENCODING=utf-8

curl -s "https://www.edsm.net/api-v1/systems?showId=1&coords=1&submitted=1&showInformation=1&showPrimaryStar=1&showPermit=1&startDateTime=${STARTDATE}&endDateTime=${ENDDATE}" | 
	jq -c '.[]' | 
	bzip2 >"${EDSMDIR}/systems-${DATE}.jsonl.bz2.tmp"
mv "${EDSMDIR}/systems-${DATE}.jsonl.bz2.tmp" "${EDSMDIR}/systems-${DATE}.jsonl.bz2"

if (( $(stat -c '%Y' "${EDSMDIR}/bodies.jsonl.bz2") < $(date +%s --date="$(curl -s -I 'https://www.edsm.net/dump/bodies.json' | sed -n 's/^Last-Modified: //p')") )); then
  curl -s "https://www.edsm.net/dump/bodies.json" | "${SCRIPTSDIR}/jsontojsonl.py" | bzip2 >"${EDSMDIR}/bodies.jsonl.bz2.tmp"
  mv "${EDSMDIR}/bodies.jsonl.bz2.tmp" "${EDSMDIR}/bodies.jsonl.bz2"
fi

curl -s "https://www.edsm.net/dump/bodies7days.json" | "${SCRIPTSDIR}/jsontojsonl.py" | bzip2 >"${EDSMDIR}/bodies-${DATE}.jsonl.bz2.tmp"
mv "${EDSMDIR}/bodies-${DATE}.jsonl.bz2.tmp" "${EDSMDIR}/bodies-${DATE}.jsonl.bz2"
curl -s "https://www.edsm.net/dump/systemsWithCoordinates.json" | "${SCRIPTSDIR}/jsontojsonl.py" | bzip2 >"${EDSMDIR}/systemsWithCoordinates.jsonl.bz2.tmp"
mv "${EDSMDIR}/systemsWithCoordinates.jsonl.bz2.tmp" "${EDSMDIR}/systemsWithCoordinates.jsonl.bz2"
curl -s "https://www.edsm.net/dump/systemsWithoutCoordinates.json" | "${SCRIPTSDIR}/jsontojsonl.py" | bzip2 >"${EDSMDIR}/systemsWithoutCoordinates.jsonl.bz2.tmp"
mv "${EDSMDIR}/systemsWithoutCoordinates.jsonl.bz2.tmp" "${EDSMDIR}/systemsWithoutCoordinates.jsonl.bz2"

if [ "${EDSMDIR}/bodies.jsonl.bz2" -nt "${BODIESDIR}/edsm-namedbodies.json" ]; then
  rm "${BODIESDIR}/edsm-namedbodies-cache.json"
  "${SCRIPTSDIR}/namedbodies-edsm.py" >"${BODIESDIR}/edsm-namedbodies.log"
fi
"${SCRIPTSDIR}/process_materials_edsm.sh"
