#!/bin/bash

EDDNDIR="/srv/eddata/EDDN"
ANONDIR="/srv/eddata/EDDN-anon"
SCRIPTSDIR="/srv/eddata/scripts"
BODIESDIR="/srv/eddata/namedbodies"
find "${EDDNDIR}" "${ANONDIR}" -name '*.jsonl' -mmin +60 -print0 | xargs -0 bzip2
"${SCRIPTSDIR}/namedbodies-eddn.py" >"${BODIESDIR}/eddn-namedbodies.log"
