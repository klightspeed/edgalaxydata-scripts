#!/bin/bash

DATE=$(date +%Y-%m-%d --date="now -16 hours")
EDDBDIR='/srv/eddata/EDDB'
curl -s 'https://eddb.io/archive/v5/bodies_recently.jsonl' | bzip2 >"${EDDBDIR}/bodies_recently_${DATE}.jsonl.bz2"
curl -s 'https://eddb.io/archive/v5/systems_recently.csv' | bzip2 >"${EDDBDIR}/systems_recently_${DATE}.csv.bz2"
wget 'https://eddb.io/archive/v5/systems_populated.jsonl' -O "${EDDBDIR}/systems_populated.jsonl"
wget 'https://eddb.io/archive/v5/stations.jsonl' -O "${EDDBDIR}/stations.jsonl"
wget 'https://eddb.io/archive/v5/factions.jsonl' -O "${EDDBDIR}/factions.jsonl"
wget 'https://eddb.io/archive/v5/commodities.json' -O "${EDDBDIR}/commodities.json"
wget 'https://eddb.io/archive/v5/modules.json' -O "${EDDBDIR}/modules.json"
curl -s 'https://eddb.io/archive/v5/systems.csv' | bzip2 >"${EDDBDIR}/systems.csv.bz2"

