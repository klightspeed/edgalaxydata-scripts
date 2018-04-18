#!/bin/bash

EDSMDIR="/srv/eddata/EDSM"
SCRIPTSDIR="/srv/eddata/scripts"
BODIESDIR="/srv/eddata/namedbodies"

ENDDATE="$(date +"%Y-%m-%d+%H:%M:%S" --utc --date="now + 1 hour")"
STARTDATE="$(date +"%Y-%m-%d+00:00:00" --utc --date="yesterday")"
DATE="$(date +"%Y-%m-%d" --utc)"

curl -s "https://www.edsm.net/api-v1/systems?showId=1&coords=1&submitted=1&showInformation=1&showPrimaryStar=1&showPermit=1&startDateTime=${STARTDATE}&endDateTime=${ENDDATE}" | 
	jq -c '.[]' | 
	bzip2 >"${EDSMDIR}/systems-${DATE}.jsonl.bz2"

if (( $(stat -c '%Y' "${EDSMDIR}/bodies.jsonl.bz2") < $(date +%s --date="$(curl -s -I 'https://www.edsm.net/dump/bodies.json' | sed -n 's/^Last-Modified: //p')") )); then
  curl -s "https://www.edsm.net/dump/bodies.json" | sed -n 's/^ *\([{].*[}]\),*/\1/p' | bzip2 >"${EDSMDIR}/bodies.jsonl.bz2"
fi

curl -s "https://www.edsm.net/dump/bodies7days.json" | sed 's/^ *\([{].*[}]\),*/\1/p' | bzip2 >"${EDSMDIR}/bodies-${DATE}.jsonl.ba2"
curl -s "https://www.edsm.net/dump/systemsWithCoordinates.json" | sed -n 's/^ *\([{].*[}]\),*/\1/p' >"${EDSMDIR}/systemsWithCoordinates.jsonl"
curl -s "https://www.edsm.net/dump/systemsWithoutCoordinates.json" | sed -n 's/^ *\([{].*[}]\),*/\1/p' >"${EDSMDIR}/systemsWithoutCoordinates.jsonl"

"${SCRIPTSDIR}/namedbodies-edsm.py" >"${BODIESDIR}/edsm-namedbodies.log"
"${SCRIPTSDIR}/process_materials_edsm.sh"
