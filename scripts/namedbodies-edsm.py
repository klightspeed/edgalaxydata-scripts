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

edsmdir   = '/srv/eddata/EDSM'
bodiesdir = '/srv/eddata/namedbodies'

revpgsysre = re.compile('[0-9]+(-[0-9]+)?[a-h] [a-z]-[a-z][a-z] ')
pgre = re.compile(' [a-z][a-z]-[a-z] [a-h][0-9]')
desigre = re.compile('( [a-h]|( a?b?c?d?e?f?g?h?)? ([1-9][0-9]*( [a-z]( [a-z]( [a-z])?)?)?|[a-h] belt cluster [1-9][0-9]*))$')
sdesigre = re.compile(' [a-h]$')

bodiesfile       = edsmdir   + '/bodies.jsonl.bz2'
bodiesdeltaglob  = edsmdir   + '/bodies-*.jsonl.bz2'
syscleanupfile   = bodiesdir + '/syscleanup.txt'
sysrenamefile    = bodiesdir + '/renamed-systems.txt'
outfile_mismatch = bodiesdir + '/edsm-bodymismatch.json'
outfile_named    = bodiesdir + '/edsm-namedbodies.json'
cachefile_named  = bodiesdir + '/edsm-namedbodies-cache.json'

sheeturi = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vR9lEav_Bs8rZGRtwcwuOwQ2hIoiNJ_PWYAEgXk7E3Y-UD0r6uER04y4VoQxFAAdjMS4oipPyySoC3t/pub?gid=711269421&single=true&output=tsv'

def tojournal(body):
    j = {}
    j['edsmsysid'] = body['systemId']
    j['timestamp'] = body['updateTime'] + 'Z'
    j['BodyName'] = body['name']
    j['StarSystem'] = body['systemName']
    if body['id64'] is not None:
        j['BodyID'] = body['id64'] >> 55
    if body['systemId64'] is not None:
        j['SystemAddress'] = body['systemId64']
    j['edsmdata'] = body
    return j

def loadKnownBodies():
    knownbodies = set()
    with urllib.request.urlopen(sheeturi) as f:
        for line in f:
            fields = line.decode('utf-8').strip().split('\t')
            if len(fields) >= 5 and fields[0] != 'SystemAddress' and fields[0] != '':
                key = fields[2].lower() + ':' + fields[4].lower()
                knownbodies.add(key)
    return knownbodies

def loadSysCleanup():
    syscleanup = set()
    with open(syscleanupfile, 'r') as f:
        for line in f:
            key = line.strip().lower()
            syscleanup.add(key)
    return syscleanup

def loadSysRename():
    sysrename = {}
    with open(sysrenamefile, 'r') as f:
        for line in f:
            oldsys, newsys = line.strip().lower().split(',', 1)
            if newsys is not None:
                if newsys not in sysrename:
                    sysrename[newsys] = []
                sysrename[newsys] += [oldsys]
    return sysrename

def loadCache():
    systems = {}
    knownbyname = {}
    rejects = {}
    excludefiles = set()

    if os.path.exists(cachefile_named):
        try:
            with open(cachefile_named, 'r') as f:
                cachedata = json.load(f)
                excludefiles = set(cachedata['files'])
                rejects = cachedata['rejects']
                systems = { sysid: System(sysid, bodies) for sysid, bodies in cachedata['systems'].items() }
                knownbyname = { 
                    name: [KnownBody(body) for body in bodies] 
                        for name, bodies in cachedata['knownbyname'].items()
                }
        except:
            pass

    return (systems, knownbyname, rejects, excludefiles)

def saveCache(systems, knownbyname, rejectstore, excludefiles):
    with open(cachefile_named + '.tmp', 'w', encoding='utf-8') as f:
        json.dump({
            'files': list(excludefiles),
            'rejects': rejectstore.rejects,
            'systems': { sysid: system.todict() for sysid, system in systems.items() },
            'knownbyname': {
                name: [body.todict() for body in bodies]
                    for name, bodies in knownbyname.items()
            }
        }, f)

def saveNamedBodies(systems, knownbodies, knownbyname, rejectstore):
    with open(outfile_named + '.tmp', 'w', encoding='utf-8') as o:
        o.write('[\n  ')
        ol = 0
        for sysid, system in systems.items():
            sysbodies = system.processBodiesPass2(knownbodies, knownbyname, rejectstore)

            if sysbodies is not None:
                for j in sysbodies:
                    if ol != 0:
                        o.write(',\n  ')
                    o.write(json.dumps(j, sort_keys=True))
                    ol = ol + 1
            
        o.write('\n]\n')

def processBodiesPass1(systems, knownbodies, knownbyname, rejectstore, sysrename, excludefiles):
    filenames = [bodiesfile] + sorted(glob.glob(bodiesdeltaglob))
    for fn in filenames:
        if fn not in excludefiles:
            with bz2.BZ2File(fn, 'r') as f:
                system = None
                for line in f:
                    body = Body(json.loads(line.decode('utf-8')))
                    if system is None or system.sysid != body.sysid:
                        if body.sysid in systems:
                            system = systems[body.sysid]
                        else:
                            system = System(body.sysid)
                    
                    system.processBodyPass1(body, rejectstore, systems, knownbodies, knownbyname, sysrename)

            excludefiles.add(fn)

class RejectStore:
    def __init__(self, m, rejects):
        self.ml = 0
        self.rejects = rejects or {}
        self.m = m

    def __enter__(self):
        self.m.write('[\n  ')
        for bid, reject in self.rejects.items():
            self.store(reject)
        return self

    def __exit__(self, type, value, traceback):
        if type is None:
            self.m.write('\n]\n')

    def add(self, body, rejectType, rejectReason):
        self.store(body, rejectType = rejectType, rejectReason = rejectReason)
        self.rejects[body['id']] = body

    def store(self, body, rejectType = None, rejectReason = None):
        name = body['name'].lower()
        sysname = body['systemName'].lower()
        ts = body['updateTime']
        if rejectType is not None:
            body['rejectType'] = rejectType
        else:
            rejectType = body['rejectType']
        if rejectReason is not None:
            body['rejectReason'] = rejectReason
        else:
            rejectReason = body['rejectReason']
        j = tojournal(body)
        if self.ml != 0:
            self.m.write(',\n  ')
        self.m.write(json.dumps(j, sort_keys=True))
        self.ml = self.ml + 1
        print("[{0}] {1}:  {2} / {3} : {4}".format(ts, rejectType, sysname, name, rejectReason))

class Body:
    def __init__(self, body):
        self.body = body
        self.id = body['id']
        self.sysid = body['systemId']
        self.name = body['name'].lower()
        self.sysname = body['systemName'].lower()
        self.sma = body['semiMajorAxis']
        self.aop = body['argOfPeriapsis']
        self.inclin = body['orbitalInclination']
        self.bodyid = body['bodyId']
        self.ts = body['updateTime']
        self.disc = body['discovery']
        self.offset = body['offset']
        self.desig = None
        self.ispgdesig = False
        self.isbadpgsys = False

        if self.name.startswith(self.sysname):
            self.desig = self.name[len(self.sysname):]
            if (self.sma is None and self.name == self.sysname) or desigre.match(self.desig):
                self.ispgdesig = True
        elif pgre.search(self.name):
            self.isbadpgsys = True

    def isrenamedsys(self, sysrename):
        sysname = self.sysname
        name = self.name
        if sysname in sysrename and not name.startswith(sysname):
            if any([name == oldsys or name.startswith(oldsys + ' ') for oldsys in sysrename[sysname]]):
                return True
        return False

    def addknownbody(self, knownbodies, knownbyname):
        kskey = self.sysname + ':' + self.name
        sysname = self.sysname
        name = self.name
        if kskey in knownbodies or (self.ispgdesig and not revpgsysre.match(sysname[::-1])):
            if name not in knownbyname:
                knownbyname[name] = []
            knownbyname[name] += [KnownBody(self.body)]
            print("[{0}] Namedsys:  {1} / {2}".format(self.ts, sysname, name))

    def isgood(self, knownbodies):
        kskey = self.sysname + ':' + self.name
        sysname = self.sysname
        name = self.name
        if kskey in knownbodies or (name == sysname and self.sma is not None and self.sma != 0):
            return True
        elif not name.startswith(sysname) and not self.isbadpgsys:
            return True

    def findDuplicate(self, knownbodies, knownbyname):
        kskey = self.sysname + ':' + self.name
        if self.name in knownbyname and kskey not in knownbodies:
            for dup in knownbyname[self.name]:
                if dup.id != self.id:
                    if self.sma is None and dup.sma is None:
                        return dup
                    elif self.aop is not None and dup.aop is not None and self.inclin is not None and dup.inclin is not None:
                        if abs(self.aop - dup.aop) < 0.01 and abs(self.inclin - dup.inclin) < 0.01:
                            return dup

class KnownBody:
    def __init__(self, body):
        self.id = body['id']
        self.sma = body['semiMajorAxis']
        self.aop = body['argOfPeriapsis']
        self.inclin = body['orbitalInclination']
        self.sysname = intern(body['systemName'])

    def todict(self):
        return {
            'id': self.id,
            'semiMajorAxis': self.sma,
            'argOfPeriapsis': self.aop,
            'orbitalInclination': self.inclin,
            'systemName': self.sysname
        }

class System:
    def __init__(self, sysid, bodies = None):
        self.sysid = sysid
        self.bodies = {}
        if bodies is not None:
            self.bodies = { bid: Body(body) for bid, body in bodies.items() }

    def add(self, body):
        self.bodies[body.id] = body

    def processBodyPass1(self, body, rejectstore, systems, knownbodies, knownbyname, sysrename):
        addsys = False

        if body.id in rejectstore.rejects:
            return
        
        if body.isrenamedsys(sysrename):
            rejectstore.add(body.body, 'Rejected', 'Body with old system name')
            return

        if body.isgood(knownbodies):
            addsys = True
        elif body.isbadpgsys:
            rejectstore.add(body.body, 'Mismatch', 'Procgen body in wrong system')
            return

        body.addknownbody(knownbodies, knownbyname)

        self.add(body)

        if body.sysid in systems:
            print('[{0}] Processing {1} / {2}'.format(body.ts, body.sysname, body.name))
        elif addsys:
            systems[body.sysid] = self
            for bid, b in self.bodies.items():
                print('[{0}] Processing {1} / {2}'.format(b.ts, b.sysname, b.name))

    def processBodiesPass2(self, knownbodies, knownbyname, rejectstore):
        isnamed = self.isnamed()
        sysbodies = []
        addsys = False

        for bid, body in self.bodies.items():
            kskey = body.sysname + ':' + body.name
            j = tojournal(body.body)
            isdup = False
            ispgdesig = False
            desig = None
            mismatchreason = None

            dup = body.findDuplicate(knownbodies, knownbyname)
            if dup:
                isdup = True
                mismatchreason = 'Duplicate of body in {0}'.format(dup.sysname)

            if (isnamed and not isdup and not body.ispgdesig) or kskey in knownbodies:
                addsys = True
                sysbodies += [j]
                print("[{0}] Named:    {1} / {2}".format(body.ts, body.sysname, body.name))
            elif body.ispgdesig:
                if len(body.desig) == 2 and sdesigre.match(body.desig):
                    sysbodies += [j]
                print("[{0}] Desig:    {1} / {2}".format(body.ts, body.sysname, body.name))
            elif mismatchreason is None and body.ts > '2016-11-01' and body.ts[:10] != '2017-04-04':
                addsys = True
                sysbodies += [j]
                print("[{0}] Unknown:  {1} / {2}".format(body.ts, body.sysname, body.name))
            else:
                if mismatchreason is None:
                    mismatchreason = 'Misnamed body or wrong system'
                rejectstore.store(body.body, 'Mismatch', mismatchreason)

        if addsys:
            return sysbodies

    def isnamed(self):
        isnamed = False
        for bid, body in self.bodies.items():
            kskey = body.sysname + ':' + body.name
            if (body.name == body.sysname and body.sma is not None and body.sma != 0):
                isnamed = True
        return isnamed

    def todict(self):
        return { bid: body.body for bid, body in self.bodies.items() }

def main():
    print('Loading known bodies')
    knownbodies = loadKnownBodies()
    print('Loading renamed systems')
    sysrename = loadSysRename()
    print('Loading cache')
    systems, knownbyname, rejects, excludefiles = loadCache()

    with open(outfile_mismatch + '.tmp', 'w', encoding='utf-8') as m, RejectStore(m, rejects) as rejectstore:
        print('Processing bodies')
        processBodiesPass1(systems, knownbodies, knownbyname, rejectstore, sysrename, excludefiles)

        print('Saving cache')
        saveCache(systems, knownbyname, rejectstore, excludefiles)

        print('Saving named bodies')
        saveNamedBodies(systems, knownbodies, knownbyname, rejectstore)

    os.rename(outfile_mismatch + '.tmp', outfile_mismatch)
    os.rename(outfile_named + '.tmp', outfile_named)
    os.rename(cachefile_named + '.tmp', cachefile_named)

if __name__ == '__main__':
    main()
