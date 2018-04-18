#!/bin/bash

cd "/srv/eddata/materials"
#wget -N 'https://eddb.io/archive/v5/bodies.jsonl'
if [[ "bodies.jsonl" -nt "eddbmaterials.json" || "process_materials.py" -nt "eddbmaterials.json" ]]; then
  ./process_materials.py >eddbmaterials.json
fi
jq -c '.[] |= (.materials as $materials | .volcanism | with_entries(.key as $vt | (.value |= ($materials | (.[] |= .byvolcanism[$vt]) | del(.[] | nulls)))))' eddbmaterials.json >volcanism.json
jq -c '.[] |= (.materials as $materials | .temperature | with_entries(.key as $tt | (.value |= ($materials | (.[] |= .bytemperature[$tt]) | del(.[] | nulls)))))' eddbmaterials.json >temperature.json
jq -c '.[] |= .volctemp' eddbmaterials.json >volctemp.json
jq -c '.[] |= (.materials as $materials | .volctemp | with_entries(.key as $tt | (.value |= with_entries(.key as $vt | (.value |= ($materials | (.[] |= .byvolctemp[$tt][$vt]) | del(.[] | nulls)))))))' eddbmaterials.json >volctempdetail.json
jq -c '.[] |= (.materials | with_entries(.value |= .foundwithrare) | del(.[] | nulls))' eddbmaterials.json >foundwithrare.json
jq -c '.[] |= (.materials | with_entries(.value |= .foundwith) | del(.[] | nulls))' eddbmaterials.json >foundwith.json
jq -c '.[] |= (.materials | with_entries(.value |= {mintemperature, meantemperature, maxtemperature}))' eddbmaterials.json >tempstats.json
jq -c '.[] |= (.materials | with_entries(.value |= {count, mean, median, mode, share}))' eddbmaterials.json >materials.json
jq -c '.[] |= (.materials | with_entries(.value |= .aggregate) | del(.[] | nulls))' eddbmaterials.json >aggregate.json
