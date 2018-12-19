#!/bin/bash

cd /srv/eddata/stellardist

if [[ '/srv/eddata/EDSM/bodies.jsonl.bz2' -nt stellardist.json || /srv/eddata/scripts/stellardist-edsm.py -nt stellardist.json ]]; then
    /srv/eddata/scripts/stellardist-edsm.py >stellardist.json.tmp && mv stellardist.json.tmp stellardist.json
fi

jq '[{bxz400,bxz1000,bxz2000,by1000,bout} | to_entries | .[] | .key[1:] as $zone | .value | to_entries | .[] | .key as $startype | .value.massclass | to_entries | .[] | .key as $massclass | .value.age | to_entries | .[] | (if (.key == "0") then 0 else (.key | tonumber | . / 10.0 | exp | -. | floor | -.) end) as $val | {"StarType":$startype, "SizeClass":$massclass, "Value":$val, "LogValue":.key, "Zone":$zone, "Count":.value}]' stellardist.json >stellardist-edsm-age.json
jq '[{bxz400,bxz1000,bxz2000,by1000,bout} | to_entries | .[] | .key[1:] as $zone | .value | to_entries | .[] | .key as $startype | .value.massclass | to_entries | .[] | .key as $massclass | .value.mass | to_entries | .[] | (.key | tonumber | . / 10.0 | exp) as $val | {"StarType":$startype, "SizeClass":$massclass, "Value":$val, "LogValue":.key, "Zone":$zone, "Count":.value}]' stellardist.json >stellardist-edsm-mass.json
jq '[{bxz400,bxz1000,bxz2000,by1000,bout} | to_entries | .[] | .key[1:] as $zone | .value | to_entries | .[] | .key as $startype | .value.massclass | to_entries | .[] | .key as $massclass | .value.radius | to_entries | .[] | (.key | tonumber | . / 10.0 | exp) as $val | {"StarType":$startype, "SizeClass":$massclass, "Value":$val, "LogValue":.key, "Zone":$zone, "Count":.value}]' stellardist.json >stellardist-edsm-radius.json
jq '[{bxz400,bxz1000,bxz2000,by1000,bout} | to_entries | .[] | .key[1:] as $zone | .value | to_entries | .[] | .key as $startype | .value.massclass | to_entries | .[] | .key as $massclass | .value.temperature | to_entries | .[] | (if (.key == "0") then 0 else (.key | tonumber | . / 10.0 | exp) end) as $val | {"StarType":$startype, "SizeClass":$massclass, "Value":$val, "LogValue":.key, "Zone":$zone, "Count":.value}]' stellardist.json >stellardist-edsm-temperature.json
jq '.bycoord' stellardist.json >stellardist-edsm-bycoord.json

