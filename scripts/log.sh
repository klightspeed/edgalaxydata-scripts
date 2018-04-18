#!/bin/bash

LOGDIR="/srv/eddata/log"

logname="$1"
shift

"$@" >"${LOGDIR}/$(date +"%Y-%m-%d")-${logname}.log" 2>&1
