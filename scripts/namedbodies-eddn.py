#!/usr/bin/python3

from sys import intern
import sys
import bz2
import json
from collections import OrderedDict
import re
import urllib.request
import glob
import os
import os.path

eddndir   = '/srv/eddata/EDDN-anon'
bodiesdir = '/srv/eddata/namedbodies'

revpgsysre = re.compile('[0-9]+(-[0-9]+)?[a-h] [a-z]-[a-z][a-z] ')
pgre = re.compile(' [a-z][a-z]-[a-z] [a-h][0-9]')
desigre = re.compile('( [a-h]|( a?b?c?d?e?f?g?h?){0,1} ([1-9][0-9]*( [a-z]( [a-z]( [a-z])?)?)?( [a-h] ring)?|[a-h] belt cluster [1-9][0-9]*))$')
sdesigre = re.compile(' [a-h]$')

srcglob          = eddndir   + '/Journal.Scan-*.jsonl.bz2'
syscleanupfile   = bodiesdir + '/syscleanup.txt'
sysrenamefile    = bodiesdir + '/renamed-systems.txt'
outfile_named    = bodiesdir + '/eddn-namedbodies.json'
cachefile_named  = bodiesdir + '/eddn-namedbodies-cache.json'
rejectfile_named = bodiesdir + '/eddn-namedbodies-rejected.json'
softwarefile     = bodiesdir + '/eddn-namedbodies-software.json'

sheeturi = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR9lEav_Bs8rZGRtwcwuOwQ2hIoiNJ_PWYAEgXk7E3Y-UD0r6uER04y4VoQxFAAdjMS4oipPyySoC3t/pub?gid=711269421&single=true&output=tsv'

badsys_3_0_2 = set([
])

badsys_2_4_x = set([
    'bragurom du'
])

badsys_2_3_10 = set([
    'ratri',
    'ogma'
])

def tojournal(body, msg):
    j = {}
    j['timestamp'] = body['timestamp']
    j['BodyName'] = body['BodyName']
    j['StarSystem'] = body['StarSystem']
    if 'BodyID' in body:
        j['BodyID'] = body['BodyID']
    if 'SystemAddress' in body:
        j['SystemAddress'] = body['SystemAddress']
    j['journal'] = body
    j['msgheader'] = msg['header']
    return j

def main():
    knownbodies = set()
    with urllib.request.urlopen(sheeturi) as f:
        for line in f:
            fields = line.decode('utf-8').strip().split('\t')
            if len(fields) >= 5 and fields[0] != 'SystemAddress' and fields[0] != '':
                key = fields[2].lower() + ':' + fields[4].lower()
                knownbodies.add(key)
    syscleanup = set()
    with open(syscleanupfile, 'r') as f:
        for line in f:
            key = line.strip().lower()
            syscleanup.add(key)
    sysrename = {}
    with open(sysrenamefile, 'r') as f:
        for line in f:
            oldsys, newsys = line.strip().lower().split(',', 1)
            if newsys is not None:
                if newsys not in sysrename:
                    sysrename[newsys] = []
                sysrename[newsys] += [oldsys]
    systems = {}
    knownbyname = {}
    excludefiles = set()
    rejectedbodies = []
    software = {}

    if os.path.exists(cachefile_named):
        try:
            with open(cachefile_named, 'r') as f:
                cachedata = json.load(f)
                excludefiles = set(cachedata['files'])
                systems = cachedata['systems']
                knownbyname = cachedata['knownbyname']
                rejectedbodies = cachedata['rejects']
                software = cachedata['software']
        except:
            pass

    for fn in sorted(glob.glob(srcglob)):
        if fn in excludefiles:
            continue
        print(fn)
        with bz2.BZ2File(fn, 'r') as f:
            for line in f:
                try:
                    msg = json.loads(line.decode('utf-8'))
                    body = msg['message']
                    if 'uploaderID' in msg['header']:
                        del msg['header']['uploaderID']
                    if 'timestamp' not in body:
                        continue
                except:
                    print('Error: {0}'.format(sys.exc_info()[0]))
                    pass
                else:
                    name = body['BodyName'].lower()
                    sysname = body['StarSystem'].lower()
                    sysid = body['SystemAddress'] if 'SystemAddress' in body else None
                    sma = body['SemiMajorAxis'] if 'SemiMajorAxis' in body else None
                    ts = body['timestamp']
                    aop = body['Periapsis'] if 'Periapsis' in body else None
                    inclin = body['OrbitalInclination'] if 'OrbitalInclination' in body else None
                    bodyid = body['BodyID'] if 'BodyID' in body else None
                    kskey = sysname + ':' + name
                    nbody = msg
                    addsys = False
                    desig = None
                    ispgdesig = False

                    softwareName = msg['header']['softwareName']
                    softwareVersion = msg['header']['softwareVersion']
                    softwareNameVer = softwareName + '\t' + softwareVersion

                    if softwareNameVer not in software:
                        software[softwareNameVer] = { 
                            'name': softwareName, 
                            'version': softwareVersion, 
                            'total': 0
                        }

                    software[softwareNameVer]['total'] += 1
                
                    if sysname in sysrename and not name.startswith(sysname):
                        if any(name == oldsys or (name.startswith(oldsys.lower() + ' ') and desigre.match(name[len(oldname):])) for oldsys in sysrename[sysname]):
                            print("[{0}] Rejected: {1} / {2} : Body with old system name".format(ts, sysname, name))
                            msg['reject'] = {'type': 'OldName', 'reason': 'Body with old system name'}
                            rejectedbodies += [msg]
                            continue

                    if sysname in badsys_2_3_10 and ts >= '2017-06-26' and ts < '2017-09-26':
                        continue
                    elif sysname in badsys_2_4_x and ts >= '2017-09-26' and ts <= '2018-02-27':
                        continue
                    elif sysname in badsys_3_0_2 and ts >= '2018-03-06' and ts <= '2018-03-19':
                        continue

                    if name.startswith(sysname):
                        desig = name[len(sysname):]
                        if (sma is None and name == sysname) or desigre.match(desig):
                            ispgdesig = True

                    if (name == sysname and aop is None and inclin is None and sma is None) or ' belt cluster ' in name:
                        aop = 0
                        inclin = 0
                        sma = 0
                    elif aop is None or inclin is None:
                        print('[{0}] Rejected:  {1} / {2} : Periapsis or Inclination missing'.format(ts, sysname, name))
                        continue
                        
                    if kskey in knownbodies or (ispgdesig and not revpgsysre.match(sysname[::-1])):
                        if name not in knownbyname:
                            knownbyname[name] = []
                        kbindex = None
                        kbody = {
                            'timestamp': body['timestamp'],
                            'StarSystem': intern(body['StarSystem']),
                            'SystemAddress': sysid,
                            'BodyID': bodyid,
                            'SemiMajorAxis': sma or 0,
                            'Periapsis': aop or 0,
                            'OrbitalInclination': inclin or 0
                        }
                        for i, kb in enumerate(knownbyname[name]):
                            if kb['StarSystem'].lower() == sysname:
                                kbaop = kb['Periapsis']
                                kbinclin = kb['OrbitalInclination']
                                kbbodyid = kb['BodyID'] if 'BodyID' in kb else None
                                kbsysid = kb['SystemAddress'] if 'SystemAddress' in kb else None
                                if abs(kbaop - aop) < 0.01 and abs(kbinclin - inclin) < 0.01 and (kbbodyid is None or bodyid is None or kbbodyid == bodyid):
                                    kbindex = i

                        if kbindex is not None:
                            kb = knownbyname[name][kbindex]
                            if (kb['timestamp'] < ts or (kbbodyid is None and bodyid is not None)) and (kbbodyid is None or (bodyid is not None and bodyid == kbbodyid)):
                                knownbyname[name][kbindex] = kbody
                        else:
                            knownbyname[name] += [kbody]

                    if kskey in knownbodies or (name == sysname and sma != 0):
                        nbody = msg
                        addsys = True
                    elif not name.startswith(sysname):
                        if pgre.search(name):
                            print("[{0}] Mismatch:  {1} / {2} : Procgen body in wrong system".format(ts, sysname, name))
                            msg['reject'] = {'type': 'Mismatch', 'reason': 'Procgen body in wrong system'}
                            rejectedbodies += [msg]
                            nbody = None
                        else:
                            nbody = msg
                            addsys = True

                    if nbody is not None:
                        if addsys and sysname not in systems:
                            systems[sysname] = []
                        if sysname in systems:
                            kbindex = None
                            kbfound = False
                            kbody = None

                            for i, kmsg in enumerate(systems[sysname]):
                                kb = kmsg['message']
                                if kb['BodyName'].lower() == name:
                                    kbaop = kb['Periapsis'] if 'Periapsis' in kb else 0
                                    kbinclin = kb['OrbitalInclination'] if 'OrbitalInclination' in kb else 0
                                    kbbodyid = kb['BodyID'] if 'BodyID' in kb else None
                                    kbsysid = kb['SystemAddress'] if 'SystemAddress' in kb else None
                                    if abs(kbaop - aop) < 0.01 and abs(kbinclin - inclin) < 0.01 and (kbbodyid is None or bodyid is None or kbbodyid == bodyid):
                                        kbindex = i
                                        kbody = kb

                            if kbindex is not None:
                                kb = systems[sysname][kbindex]
                                kb = kb['message']
                                kbbodyid = kb['BodyID'] if 'BodyID' in kb else None
                                if kb['timestamp'] < ts or (kbbodyid is None and bodyid is not None):
                                    if (kbbodyid is None or (bodyid is not None and bodyid == kbbodyid)):
                                        print('[{0}] Updating   {1} / {2}'.format(ts, sysname, name))
                                        systems[sysname][kbindex] = msg
                                    elif bodyid is not None:
                                        print('[{0}] Rejected:  {1} / {2} : bodyid {3}.{4} != {5}.{6}'.format(ts, sysname, name, sysid, bodyid, kbsysid, kbbodyid))
                                        msg['reject'] = {'type': 'Rejected', 'reason': 'Body ID mismatch: bodyid {0}.{1} != {2}.{3}'.format(sysid, bodyid, kbsysid, kbbodyid)}
                                        rejectedbodies += [msg]
                            else:
                                print('[{0}] Processing {1} / {2}'.format(ts, sysname, name))
                                systems[sysname] += [msg]
        excludefiles.add(fn)
    
    with open(cachefile_named + '.tmp', 'w', encoding='utf-8') as f:
        json.dump({
            'files': list(excludefiles),
            'systems': systems,
            'knownbyname': knownbyname,
            'rejects': rejectedbodies,
            'software': software
        }, f)

    with open(softwarefile + '.tmp', 'w', encoding='utf-8') as f:
        json.dump(software, f)

    with open(outfile_named + '.tmp', 'w', encoding='utf-8') as o:
        o.write('[\n  ')
        ol = 0
        for sysid, esys in systems.items():
            isnamed = False
            dupbases = []
            for msg in esys:
                body = msg['message']
                name = body['BodyName'].lower()
                sysname = body['StarSystem'].lower()
                sma = body['SemiMajorAxis'] if 'SemiMajorAxis' in body else 0
                bodyid = body['BodyID'] if 'BodyID' in body else None
                if (name == sysname and sma != 0):
                    isnamed = True
                elif name != sysname and (bodyid == 0 or sma == 0):
                    dupbases += [name]

            for msg in esys:
                body = msg['message']
                name = body['BodyName'].lower()
                sysname = body['StarSystem'].lower()
                starpos = body['StarPos']
                sma = body['SemiMajorAxis'] if 'SemiMajorAxis' in body else 0
                ts = body['timestamp']
                aop = body['Periapsis'] if 'Periapsis' in body else 0
                inclin = body['Inclination'] if 'Inclination' in body else 0
                bodyid = body['BodyID'] if 'BodyID' in body else None
                kskey = sysname + ':' + name
                j = tojournal(body, msg)
                isdup = False
                ispgdesig = False
                desig = None
                mismatchreason = None #'Misnamed body or wrong system'

                if name.startswith(sysname):
                    desig = name[len(sysname):]
                    if (sma == 0 and name == sysname) or desigre.match(desig):
                        ispgdesig = True
                
                if name in knownbyname and kskey not in knownbodies:
                    for dup in knownbyname[name]:
                        if dup['timestamp'] != body['timestamp'] or dup['StarSystem'].lower() != sysname:
                            dupsma = dup['SemiMajorAxis'] if 'SemiMajorAxis' in dup else 0
                            dupaop = dup['Periapsis'] if 'Periapsis' in dup else 0
                            dupinclin = dup['Inclination'] if 'Inclination' in dup else 0
                            if (sma == 0 and dupsma == 0):
                                isdup = True
                                mismatchreason = 'Duplicate of body in {0}'.format(dup['StarSystem'])
                            elif abs(aop - dupaop) < 0.01 and abs(inclin - dupinclin) < 0.01:
                                isdup = True
                                mismatchreason = 'Duplicate of body in {0}'.format(dup['StarSystem'])

                    if not isdup:
                        for dupbase in dupbases:
                            if name.startswith(dupbase):
                                isdup = True
                                mismatchreason = 'Duplicate of body in {0}'.format(dup['StarSystem'])

                if (isnamed and not isdup and not ispgdesig) or kskey in knownbodies:
                    if ol != 0:
                        o.write(',\n  ')
                    o.write(json.dumps(j, sort_keys=True))
                    ol = ol + 1
                    print("[{0}] Named:    {1} / {2}".format(ts, sysname, name))
                elif ispgdesig:
                    if len(desig) == 2 and sdesigre.match(desig):
                        if ol != 0:
                            o.write(',\n  ')
                        o.write(json.dumps(j, sort_keys=True))
                        ol = ol + 1
                    print("[{0}] Desig:    {1} / {2}".format(ts, sysname, name))
                elif mismatchreason is None:
                    if ol != 0:
                        o.write(',\n  ')
                    o.write(json.dumps(j, sort_keys=True))
                    ol = ol + 1
                    print("[{0}] Unknown:  {1} / {2}".format(ts, sysname, name))
                else:
                    print("[{0}] Mismatch: {1} / {2} : {3}".format(ts, sysname, name, mismatchreason))
                    msg['reject'] = {'type': 'Mismatch', 'reason': mismatchreason}
                    rejectedbodies += [msg]
        o.write('\n]\n')

    with open(rejectfile_named + '.tmp', 'a', encoding='utf-8') as f:
        json.dump(rejectedbodies, f)

    os.rename(softwarefile + '.tmp', softwarefile)
    os.rename(rejectfile_named + '.tmp', rejectfile_named)
    os.rename(outfile_named + '.tmp', outfile_named)
    os.rename(cachefile_named + '.tmp', cachefile_named)

if __name__ == '__main__':
    main()
