#!/bin/bash

cd "/srv/eddata/materials"
#wget -N 'https://eddb.io/archive/v5/bodies.jsonl'
if [[ "../EDSM/bodies.jsonl.bz2" -nt "edsmmaterials.json" || "process_materials_edsm.py" -nt "edsmmaterials.json" ]]; then
  ./process_materials_edsm.py >edsmmaterials.json
fi
jq -c '.[] |= (.materials as $materials | .volcanism | with_entries(.key as $vt | (.value |= ($materials | (.[] |= .byvolcanism[$vt]) | del(.[] | nulls)))))' edsmmaterials.json >volcanism.json
jq -c '.[] |= (.materials as $materials | .temperature | with_entries(.key as $tt | (.value |= ($materials | (.[] |= .bytemperature[$tt]) | del(.[] | nulls)))))' edsmmaterials.json >temperature.json
jq -c '.[] |= .volctemp' edsmmaterials.json >volctemp.json
jq -c '.[] |= (.materials as $materials | .volctemp | with_entries(.key as $tt | (.value |= with_entries(.key as $vt | (.value |= ($materials | (.[] |= .byvolctemp[$tt][$vt]) | del(.[] | nulls)))))))' edsmmaterials.json >volctempdetail.json
jq -c '.[] |= (.materials | with_entries(.value |= .foundwithrare) | del(.[] | nulls))' edsmmaterials.json >foundwithrare.json
jq -c '.[] |= (.materials | with_entries(.value |= .foundwith) | del(.[] | nulls))' edsmmaterials.json >foundwith.json
jq -c '.[] |= (.materials | with_entries(.value |= {mintemperature, meantemperature, maxtemperature}))' edsmmaterials.json >tempstats.json
jq -c '.[] |= (.materials | with_entries(.value |= {count, mean, median, mode, share}))' edsmmaterials.json >materials.json
jq -c '.[] |= (.materials | with_entries(.value |= .aggregate) | del(.[] | nulls))' edsmmaterials.json >aggregate.json
jq -c '[ .[] | .oddballs[] | { systemId64, systemName, name, axialTilt, updateTime, subType, surfaceTemperature, materials } ] | sort_by(.surfaceTemperature)' edsmmaterials.json >oddballs.json
