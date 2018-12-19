#!/usr/bin/python

from __future__ import print_function
import json
import math
from collections import OrderedDict
from decimal import Decimal
import bz2
import time
import calendar
import sys
import re

edsmdir   = '/srv/eddata/EDSM'
starsdir  = '/srv/eddata/stellardist'

revpgsysre = re.compile('^([0-9]{1,5})(|-[0-9]{1,3})([a-h]) [a-z]-[a-z][a-z] ')
desigre = re.compile('^ [a-h]|^( a?b?c?d?e?f?g?h?)? ([1-9][0-9]*( [a-z]( [a-z]( [a-z])?)?)?)$')

bodiesfile  = edsmdir + '/bodies.jsonl.bz2'

ages = list(set([int(math.floor(math.log(float(v))*10)) for v in range(2,13065,2)]))
masses = list(set([int(math.floor(math.log(float(v)/256.0)*10)) for v in range(2,30720)]))
radii = [v for v in range(-128, 64)]
temps = [v for v in range(0,162)]

def getstars():
    bodiesprocessed = 0
    totalbodies = 0
    validbodies = 0
    stardistByType = {'in':{}, 'out':{}, 'xz400':{}, 'xz1000':{}, 'xz2000':{}}
    for bc in ['yin', 'yout', 'bycoord']:
        stardistByType[bc] = {'d':{},'e':{},'f':{},'g':{},'h':{}}

    bycoord = stardistByType['bycoord']

    with bz2.BZ2File(bodiesfile, 'r') as f:
        for line in f:
            body = json.loads(line)
            if (bodiesprocessed % 64000) == 0:
                sys.stderr.write('{0:10}  '.format(bodiesprocessed))
                sys.stderr.flush()
            bodiesprocessed = bodiesprocessed + 1
            if (bodiesprocessed % 1000) == 0:
                sys.stderr.write('.')
                if (bodiesprocessed % 64000) == 0:
                    sys.stderr.write(' {0} / {1}\n'.format(validbodies, totalbodies))
                sys.stderr.flush()
            if 'solarMasses' in body and 'solarRadius' in body and 'age' in body and 'subType' in body:
                totalbodies = totalbodies + 1
                sysname = body['systemName'].lower()
                bodyname = body['name'].lower()
                ispgdesig = False
                
                if bodyname == sysname:
                    ispgdesig = True
                elif len(bodyname) > len(sysname) and bodyname.startswith(sysname):
                    if desigre.match(bodyname[len(sysname):]):
                        ispgdesig = True
                
                if not ispgdesig:
                    #sys.stderr.write('{0} not a designator in {1}\n'.format(bodyname,sysname))
                    continue

                revpgsysmatch = revpgsysre.match(sysname[::-1])

                if not revpgsysmatch:
                    #sys.stderr.write('{0} not a procgen system\n'.format(sysname))
                    continue

                sysaddr = body['systemId64']
                massclass = sysaddr & 7
                seq = (sysaddr >> (44 - (massclass * 3))) & 0xFFFF

                if ord(revpgsysmatch.group(3)[0]) != massclass + 97:
                    sys.stderr.write('\n{0} massclass mismatch: {1} != {2}\n'.format(sysname, revpgsysmatch.group(3)[0], unichr(massclass + 97)))
                    continue
                
                if int(revpgsysmatch.group(1)[::-1]) != seq:
                    sys.stderr.write('\n{0} sequence mismatch: {1} != {2}\n'.format(sysname, int(revpgsysmatch.group(1)[::-1]), seq))
                    continue

                mass = body['solarMasses']
                radius = body['solarRadius']
                age = body['age'] or 0
                temperature = body['surfaceTemperature'] or 0

                if mass is None or mass == 0 or radius is None or radius == 0 or age is None:
                    continue

                masscode = chr(massclass + ord('a'))
                lmod = calendar.timegm(time.strptime(body['updateTime'], '%Y-%m-%d %H:%M:%S'))
                btype = body['subType']
                z = (((sysaddr >> 3) & (0x3FFF >> massclass)) << massclass) * 10 - 24105
                y = (((sysaddr >> (17 - massclass)) & (0x1FFF >> massclass)) << massclass) * 10 - 40985
                x = (((sysaddr >> (30 - (massclass * 2))) & (0x3FFF >> massclass)) << massclass) * 10 - 49985
                
                zone='out'
                z400=None
                z1000=None
                z2000=None
                yzone='yout'
                bzone='bout'
                if (x > -1000 and x < 1000) or (y > -1000 and y < 1000) or (z > -1000 and z < 1000):
                    zone='in'
                if y > -1000 and y < 1000:
                    yzone='yin'
                    bzone='by1000'
                if ((x > -2000 and x < 2000) or (z > -2000 and z < 2000)) and masscode == 'h':
                    z2000='xz2000'
                    bzone='bxz2000'
                if (x > -1000 and x < 1000) or (z > -1000 and z < 1000):
                    z1000='xz1000'
                    bzone='bxz1000'
                if (x > -400 and x < 400) or (z > -400 and z < 400):
                    z400='xz400'
                    bzone='bxz400'

                qage = str(int(math.floor(math.log(float(age))*10)) if age != 0 else 0)
                qmass = str(int(math.floor(math.log(float(mass))*10)))
                qrad = str(int(math.floor(math.log(float(radius))*10)))
                qtemp = str(int(math.floor(math.log(float(temperature))*10)) if temperature != 0 else 0)

                for szone in (szone for szone in [zone, z400, z1000, z2000, yzone, bzone] if szone is not None):
                    if szone not in stardistByType:
                        stardistByType[szone] = {}

                    stars = stardistByType[szone]

                    if btype not in stars:
                        stars[btype] = {
                            'age': {str(v): 0 for v in ages},
                            'mass': {str(v): 0 for v in masses},
                            'radius': {str(v): 0 for v in radii},
                            'temperature': {str(v): 0 for v in temps},
                            'massclass': {},
                            'starclass': {str(v): 0 for v in range(0, 8)}
                        }

                    if masscode not in stars[btype]['massclass']:
                        stars[btype]['massclass'][masscode] = {
                            'age': {str(v): 0 for v in ages},
                            'mass': {str(v): 0 for v in masses},
                            'radius': {str(v): 0 for v in radii},
                            'temperature': {str(v): 0 for v in temps},
                        }

                    dists = stars[btype]
                    dage = dists['age']
                    dmass = dists['mass']
                    drad = dists['radius']
                    dtemp = dists['temperature']
                    dcls = dists['starclass']

                    if qage not in dage:
                        dage[qage] = 0
                    if qmass not in dmass:
                        dmass[qmass] = 0
                    if qrad not in drad:
                        drad[qrad] = 0
                    if qtemp not in dtemp:
                        dtemp[qtemp] = 0

                    dage[qage] += 1
                    dmass[qmass] += 1
                    drad[qrad] += 1
                    dtemp[qtemp] += 1
                    dcls[str(massclass)] += 1

                    dists = dists['massclass'][masscode]
                    dage = dists['age']
                    dmass = dists['mass']
                    drad = dists['radius']
                    dtemp = dists['temperature']

                    if qage not in dage:
                        dage[qage] = 0
                    if qmass not in dmass:
                        dmass[qmass] = 0
                    if qrad not in drad:
                        drad[qrad] = 0
                    if qtemp not in dtemp:
                        dtemp[qtemp] = 0

                    dage[qage] += 1
                    dmass[qmass] += 1
                    drad[qrad] += 1
                    dtemp[qtemp] += 1

                if massclass >= 3:
                    cx = (x + 49985) / (10 << massclass)
                    cy = (y + 40985) / (10 << massclass)
                    cz = (z + 24105) / (10 << massclass)

                    for d_coord in [bycoord[masscode], stardistByType[yzone][masscode]]:
                        for dbtype in [btype, 'all']:
                            if dbtype not in d_coord:
                                d_coord[dbtype] = {'x': {}, 'y': {}, 'z': {}}

                            dists = d_coord[dbtype]
                            if cx not in dists['x']:
                                dists['x'][cx] = {'count':0,'minage':15000,'maxage':0,'sumage':0,'minmass':120,'maxmass':0,'summass':0,'minrad':512,'maxrad':0,'sumrad':0}
                            if cy not in dists['y']:
                                dists['y'][cy] = {'count':0,'minage':15000,'maxage':0,'sumage':0,'minmass':120,'maxmass':0,'summass':0,'minrad':512,'maxrad':0,'sumrad':0}
                            if cz not in dists['z']:
                                dists['z'][cz] = {'count':0,'minage':15000,'maxage':0,'sumage':0,'minmass':120,'maxmass':0,'summass':0,'minrad':512,'maxrad':0,'sumrad':0}
                            if False and cx not in dists['xz']:
                                dists['xz'][cx] = {}
                            if False and cz not in dists['xz'][cx]:
                                dists['xz'][cx][cz] = {'count':0,'minage':15000,'maxage':0,'sumage':0,'minmass':120,'maxmass':0,'summass':0,'minrad':512,'maxrad':0,'sumrad':0}

                            for blk in [dists['x'][cx], dists['y'][cy], dists['z'][cz]]: #, dists['xz'][cx][cz]]:
                                blk['count'] += 1
                                blk['sumage'] += age
                                blk['summass'] += mass
                                blk['sumrad'] += radius
                                if age < blk['minage']:
                                    blk['minage'] = age
                                if age > blk['maxage']:
                                    blk['maxage'] = age
                                if mass < blk['minmass']:
                                    blk['minmass'] = mass
                                if mass > blk['maxmass']:
                                    blk['maxmass'] = mass
                                if radius < blk['minrad']:
                                    blk['minrad'] = radius
                                if radius > blk['maxrad']:
                                    blk['maxrad'] = radius

                validbodies += 1

    sys.stderr.write(' {0} / {1}\n'.format(validbodies, totalbodies))

    return stardistByType

def main():
    print(json.dumps(getstars()))

if __name__ == '__main__':
    main()
