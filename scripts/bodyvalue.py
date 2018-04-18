#!/usr/bin/python3

import sys
import json

def bodyvalue(body):
    subType = body['subType']
    
    if subType is None:
        return 0

    if body['type'] == 'Star':
        mass = body['solarMasses']
        kval = 2880

        if mass is None:
            mass = 1.0

        if body['subType'].startswith('White Dwarf'):
            kval = 33737
        elif body['subType'] == 'Neutron Star' or body['subType'] == 'Black Hole':
            kval = 54309

        return int(kval + (mass * kval / 66.25))
    elif body['type'] == 'Planet':
        kval = 720
        mass = body['earthMasses']
        terraformable = True if body['terraformingState'] == 'Candidate for terraforming' else False

        if mass is None:
            mass = 1.0

        if subType == 'Metal rich body':
            kval = 52292
        elif subType == 'High metal content body' or subType == 'Sudarsky class II gas giant':
            kval = 23168
            if terraformable:
                kval += 241607
        elif subType == 'Earth-like world':
            kval = 155581 + 279088
        elif subType == 'Water world':
            kval = 155581
            if terraformable:
                kval += 279088
        elif subType == 'Ammonia world':
            kval = 232619
        elif subType == 'Sudarsky class I gas giant':
            kval = 3974
        else:
            kval = 720
            if terraformable:
                kval += 223971

        return int(kval + (3 * kval * (mass ** 0.199977) / 5.3))

lastsysid = None
lastsysname = None
sysval = 0

for line in sys.stdin:
    body = json.loads(line)
    sysid = body['systemId64']
    sysname = body['systemName']
    val = bodyvalue(body)
    if sysid != lastsysid:
        if lastsysname is not None:
            print('{0} [{1}]: {2}'.format(lastsysid, lastsysname, sysval))
        lastsysname = sysname
        lastsysid = sysid
        sysval = 0
    sysval = sysval + val

if lastsysname is not None:
    print('{0} [{1}]: {2}'.format(lastsysid, lastsysname, sysval))

