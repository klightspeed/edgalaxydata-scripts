#!/bin/bash

DATE=$(date +%Y-%m-%d --date="now -16 hours")
EDDBDIR='/srv/eddata/EDDB'
wget 'https://eddb.io/archive/v5/bodies_recently.jsonl' -O "${EDDBDIR}/bodies_recently_${DATE}.jsonl"
wget 'https://eddb.io/archive/v5/systems_recently.csv' -O "${EDDBDIR}/systems_recently_${DATE}.csv"
wget 'https://eddb.io/archive/v5/systems_populated.jsonl' -O "${EDDBDIR}/systems_populated.jsonl"
wget 'https://eddb.io/archive/v5/stations.jsonl' -O "${EDDBDIR}/stations.jsonl"
wget 'https://eddb.io/archive/v5/factions.jsonl' -O "${EDDBDIR}/factions.jsonl"
wget 'https://eddb.io/archive/v5/commodities.json' -O "${EDDBDIR}/commodities.json"
wget 'https://eddb.io/archive/v5/modules.json' -O "${EDDBDIR}/modules.json"
wget -N 'https://eddb.io/archive/v5/systems.csv' -O "${EDDBDIR}/systems.csv"
find ${EDDBDIR} -name 'bodies_recently_*.jsonl' -mtime +2 -print0 | xargs -0 bzip2
find ${EDDBDIR} -name 'systems_recently_*.csv' -mtime +2 -print0 | xargs -0 bzip2

