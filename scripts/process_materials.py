#!/usr/bin/python

from __future__ import print_function
import json
import math
from collections import OrderedDict
from decimal import Decimal

class Materials:
    def __init__(self):
        self.Types = {
            # Very Common
            'Carbon': {'rarity': 'Very Common', 'symbol': 'C'},
            'Iron': {'rarity': 'Very Common', 'symbol': 'Fe'},
            'Nickel': {'rarity': 'Very Common', 'symbol': 'Ni'},
            'Phosphorus': {'rarity': 'Very Common', 'symbol': 'P'},
            'Sulphur': {'rarity': 'Very Common', 'symbol': 'S'},
            # Common
            'Arsenic': {'rarity': 'Common', 'symbol': 'As'},
            'Chromium': {'rarity': 'Common', 'symbol': 'Cr'},
            'Germanium': {'rarity': 'Common', 'symbol': 'Ge'},
            'Manganese': {'rarity': 'Common', 'symbol': 'Mn'},
            'Selenium': {'rarity': 'Common', 'symbol': 'Se'},
            'Vanadium': {'rarity': 'Common', 'symbol': 'V'},
            'Zinc': {'rarity': 'Common', 'symbol': 'Zn'},
            'Zirconium': {'rarity': 'Common', 'symbol': 'Zr'},
            # Rare
            'Cadmium': {'rarity': 'Rare', 'symbol': 'Cd'},
            'Mercury': {'rarity': 'Rare', 'symbol': 'Hg'},
            'Molybdenum': {'rarity': 'Rare', 'symbol': 'Mo'},
            'Niobium': {'rarity': 'Rare', 'symbol': 'Nb'},
            'Tin': {'rarity': 'Rare', 'symbol': 'Sn'},
            'Tungsten': {'rarity': 'Rare', 'symbol': 'W'},
            # Very Rare
            'Antimony': {'rarity': 'Very Rare', 'symbol': 'Sb'},
            'Polonium': {'rarity': 'Very Rare', 'symbol': 'Po'},
            'Ruthenium': {'rarity': 'Very Rare', 'symbol': 'Ru'},
            'Technetium': {'rarity': 'Very Rare', 'symbol': 'Tc'},
            'Tellurium': {'rarity': 'Very Rare', 'symbol': 'Te'},
            'Yttrium': {'rarity': 'Very Rare', 'symbol': 'Y'},
        }
        self.VeryCommon = {n for n, v in self.Types.iteritems() if v['rarity'] == 'Very Common'}
        self.Common = {n for n, v in self.Types.iteritems() if v['rarity'] == 'Common'}
        self.Rare = {n for n, v in self.Types.iteritems() if v['rarity'] == 'Rare'}
        self.VeryRare = {n for n, v in self.Types.iteritems() if v['rarity'] == 'Very Rare'}
        self.VeryCommonNonMetals = {'Carbon', 'Phosphorus', 'Sulphur'}

materials = Materials()
tempranges = [0, 25, 50, 75, 100, 150, 200, 250, 300, 350, 400, 500, 600, 700, 800, 1000, 1500, 2000, 3000, 4000, 5000, 7500, 10000]

def median(vals):
    n = 0
    total = sum([v for k, v in vals.iteritems()])
    vals = OrderedDict(sorted(vals.iteritems(), key=lambda v: -Decimal(v[0])))
    for k, v in vals.iteritems():
        n = n + v
        if n >= total / 2:
            return k

def mean(vals):
    total = sum([v for k, v in vals.iteritems()])
    if total:
        return math.fsum([float(k) * v for k, v in vals.iteritems()]) / total
    else:
        return 0

def getstars():
    starclasses = {}
    with open('bodies.jsonl', 'rb') as f:
        for line in f:
            body = json.loads(line)
            if body['group_name'] == 'Star':
                pass

def getmats():
    totalbodies = 0
    bodymatsByType = {}
   
    with open('bodies.jsonl', 'rb') as f:
        for line in f:
            body = json.loads(line)
            if body['is_landable'] and body['materials']:
                totalbodies = totalbodies + 1
                lmod = body['updated_at']
                btype = body['type_name']
                volc = body['volcanism_type_name']
                stemp = body['surface_temperature']
                temp = '{}K'.format(max(v for v in tempranges if v < stemp)) if stemp else None
                
                vrares = [m['material_name'] for m in body['materials'] if m['material_name'] in materials.VeryRare]
                rares = [m['material_name'] for m in body['materials'] if m['material_name'] in materials.Rare]
                commons = [m['material_name'] for m in body['materials'] if m['material_name'] in materials.Common]
                vcomms = [m['material_name'] for m in body['materials'] if m['material_name'] in materials.VeryCommon]
                
                raregrp = ':'.join([m for m in materials.Rare if m in rares])
                commongrp = ':'.join([m for m in materials.Common if m in commons])

                if btype == 'Metal-rich body' and any(m for m in body['materials'] if m['material_name'] in materials.VeryCommonNonMetals):
                    pass
                elif btype != 'Metal-rich body' and stemp is not None and stemp >= 1000:
                    pass
                elif btype == 'Metal-rich body' and stemp is not None and stemp < 1000:
                    pass
                elif lmod >= 1477400000 and btype and len(vrares) == 1 and len(rares) == 2 and len(commons) == 3 and (len(vcomms) == 2 or len(vcomms) == 5):
                    vrare = vrares[0] if vrares else None

                    if btype == 'Icy body':
                        ironpct = [m['share'] for m in body['materials'] if m['material_name'] == 'Iron']
                        if ironpct[0] >= 15:
                            btype = 'Icy body (Iron rich)'
                        elif ironpct[0] < 10:
                            btype = 'Icy body (Iron poor)'

                    if btype not in bodymatsByType:
                        bodymatsByType[btype] = { 'count': 0, 'materials': {} }
                    bmbytype = bodymatsByType[btype]
                    bmbytype['count'] = bmbytype['count'] + 1

                    if stemp:
                        if 'mintemperature' not in bmbytype:
                            bmbytype['mintemperature'] = stemp
                        if stemp < bmbytype['mintemperature']:
                            bmbytype['mintemperature'] = stemp
                        if 'maxtemperature' not in bmbytype:
                            bmbytype['maxtemperature'] = stemp
                        if stemp > bmbytype['maxtemperature']:
                            bmbytype['maxtemperature'] = stemp
                        if 'meantemperature' not in bmbytype:
                            bmbytype['meantemperature'] = 0
                        if 'meantempcount' not in bmbytype:
                            bmbytype['meantempcount'] = 0
                        bmbytype['meantemperature'] = bmbytype['meantemperature'] + stemp
                        bmbytype['meantempcount'] = bmbytype['meantempcount'] + 1
                    if volc:
                        if 'volcanism' not in bmbytype:
                            bmbytype['volcanism'] = {}
                        if volc not in bmbytype['volcanism']:
                            bmbytype['volcanism'][volc] = 0
                        bmbytype['volcanism'][volc] = bmbytype['volcanism'][volc] + 1
                    if temp:
                        if 'temperature' not in bmbytype:
                            bmbytype['temperature'] = {}
                        if temp not in bmbytype['temperature']:
                            bmbytype['temperature'][temp] = 0
                        bmbytype['temperature'][temp] = bmbytype['temperature'][temp] + 1
                        if volc:
                            if 'volctemp' not in bmbytype:
                                bmbytype['volctemp'] = {}
                            if temp not in bmbytype['volctemp']:
                                bmbytype['volctemp'][temp] = {}
                            if volc not in bmbytype['volctemp'][temp]:
                                bmbytype['volctemp'][temp][volc] = 0
                            bmbytype['volctemp'][temp][volc] += 1
                    for mat in body['materials']:
                        name = mat['material_name']
                        share = mat['share']
                        if name not in bmbytype['materials']:
                            bmbytype['materials'][name] = { 'count': 0, 'share': {} }
                        bmbyname = bmbytype['materials'][name]
                        bmbyname['count'] = bmbyname['count'] + 1
                        if stemp:
                            if 'mintemperature' not in bmbyname:
                                bmbyname['mintemperature'] = stemp
                            if stemp < bmbyname['mintemperature']:
                                bmbyname['mintemperature'] = stemp
                            if 'maxtemperature' not in bmbyname:
                                bmbyname['maxtemperature'] = stemp
                            if stemp > bmbyname['maxtemperature']:
                                bmbyname['maxtemperature'] = stemp
                        if volc:
                            if 'byvolcanism' not in bmbyname:
                                bmbyname['byvolcanism'] = {}
                            if volc not in bmbyname['byvolcanism']:
                                bmbyname['byvolcanism'][volc] = { 'count': 0, 'share': {} }
                            bmbyname['byvolcanism'][volc]['count'] = bmbyname['byvolcanism'][volc]['count'] + 1
                            if temp:
                                if 'byvolctemp' not in bmbyname:
                                    bmbyname['byvolctemp'] = {}
                                if temp not in bmbyname['byvolctemp']:
                                    bmbyname['byvolctemp'][temp] = {}
                                if volc not in bmbyname['byvolctemp'][temp]:
                                    bmbyname['byvolctemp'][temp][volc] = { 'count': 0, 'share': {} }
                                bmbyname['byvolctemp'][temp][volc]['count'] += 1
                        if temp:
                            if 'bytemperature' not in bmbyname:
                                bmbyname['bytemperature'] = {}
                            if temp not in bmbyname['bytemperature']:
                                bmbyname['bytemperature'][temp] = { 'count': 0, 'share': {} }
                            bmbyname['bytemperature'][temp]['count'] = bmbyname['bytemperature'][temp]['count'] + 1
                            if 'meantemperature' not in bmbyname:
                                bmbyname['meantemperature'] = 0
                            if 'meantempcount' not in bmbyname:
                                bmbyname['meantempcount'] = 0
                            bmbyname['meantemperature'] = bmbyname['meantemperature'] + stemp
                            bmbyname['meantempcount'] = bmbyname['meantempcount'] + 1
                        if share:
                            share = str(Decimal(share).quantize(Decimal('1.0')))
                            if share not in bmbyname['share']:
                                bmbyname['share'][share] = 0
                            bmbyname['share'][share] = bmbyname['share'][share] + 1
                            if volc:
                                if share not in bmbyname['byvolcanism'][volc]['share']:
                                    bmbyname['byvolcanism'][volc]['share'][share] = 0
                                bmbyname['byvolcanism'][volc]['share'][share] = bmbyname['byvolcanism'][volc]['share'][share] + 1
                                if temp:
                                    if share not in bmbyname['byvolctemp'][temp][volc]['share']:
                                        bmbyname['byvolctemp'][temp][volc]['share'][share] = 0

                                    bmbyname['byvolctemp'][temp][volc]['share'][share] += 1
                            if temp:
                                if share not in bmbyname['bytemperature'][temp]['share']:
                                    bmbyname['bytemperature'][temp]['share'][share] = 0
                                bmbyname['bytemperature'][temp]['share'][share] = bmbyname['bytemperature'][temp]['share'][share] + 1
                        if name not in materials.VeryCommon:
                            if 'foundwith' not in bmbyname:
                                bmbyname['foundwith'] = {}
                            for mat2 in body['materials']:
                                name2 = mat2['material_name']
                                if name2 != name and name2 not in materials.VeryCommon:
                                    if name2 not in bmbyname['foundwith']:
                                        bmbyname['foundwith'][name2] = 0
                                    bmbyname['foundwith'][name2] = bmbyname['foundwith'][name2] + 1
                        if name not in materials.VeryCommon and name not in materials.VeryRare:
                            if 'foundwithrare' not in bmbyname:
                                bmbyname['foundwithrare'] = {}
                            if vrare not in bmbyname['foundwithrare']:
                                bmbyname['foundwithrare'][vrare] = {}
                            for mat2 in body['materials']:
                                name2 = mat2['material_name']
                                if name2 != name and name2 not in materials.VeryCommon and name2 not in materials.VeryRare:
                                    if name2 not in bmbyname['foundwithrare'][vrare]:
                                        bmbyname['foundwithrare'][vrare][name2] = 0
                                    bmbyname['foundwithrare'][vrare][name2] = bmbyname['foundwithrare'][vrare][name2] + 1
                        if name in materials.VeryRare:
                            if 'aggregate' not in bmbyname:
                                bmbyname['aggregate'] = {}
                            if raregrp not in bmbyname['aggregate']:
                                bmbyname['aggregate'][raregrp] = {}
                            if commongrp not in bmbyname['aggregate'][raregrp]:
                                bmbyname['aggregate'][raregrp][commongrp] = 0
                            bmbyname['aggregate'][raregrp][commongrp] = bmbyname['aggregate'][raregrp][commongrp] + 1


    for btype, bmbytype in bodymatsByType.iteritems():
        if 'meantemperature' in bmbytype:
            bmbytype['meantemperature'] = int(bmbytype['meantemperature'] * 1.0 / bmbytype['meantempcount'])
            del bmbytype['meantempcount']
        for name, bmbyname in bmbytype['materials'].iteritems():
            bmbyname['mean'] = float(Decimal(mean(bmbyname['share'])).quantize(Decimal('1.00')))
            bmbyname['median'] = float(median(bmbyname['share']))
            bmbyname['mode'] = float(max(bmbyname['share'].iteritems(), key=lambda v: (Decimal(v[0]) / 100 + v[1]))[0])
            bmbyname['symbol'] = materials.Types[name]['symbol']
            bmbyname['rarity'] = materials.Types[name]['rarity']
            if 'meantemperature' in bmbyname:
                bmbyname['meantemperature'] = bmbyname['meantemperature'] * 1.0 / bmbyname['meantempcount']
                del bmbyname['meantempcount']
            if 'byvolcanism' in bmbyname:
                for volc, bmbyvolc in bmbyname['byvolcanism'].iteritems():
                    if bmbyvolc['share']:
                        bmbyvolc['mean'] = float(Decimal(mean(bmbyvolc['share'])).quantize(Decimal('1.00')))
                        bmbyvolc['median'] = float(median(bmbyvolc['share']))
                        bmbyvolc['mode'] = float(max(bmbyvolc['share'].iteritems(), key=lambda v: (Decimal(v[0]) / 100 + v[1]))[0])
            if 'bytemperature' in bmbyname:
                for temp, bmbytemp in bmbyname['bytemperature'].iteritems():
                    if bmbytemp['share']:
                        bmbytemp['mean'] = float(Decimal(mean(bmbytemp['share'])).quantize(Decimal('1.00')))
                        bmbytemp['median'] = float(median(bmbytemp['share']))
                        bmbytemp['mode'] = float(max(bmbytemp['share'].iteritems(), key=lambda v: (Decimal(v[0]) / 100 + v[1]))[0])
            

    if True:
        return bodymatsByType
    else:
        def getmatordered(k, v):
            count = v['count']
            ret = OrderedDict([
                ('count', v['count']),
                ('mean', float(Decimal(mean(v['share'])).quantize(Decimal('1.00')))),
                ('median', float(median(v['share']))),
                ('mode', float(max(v['share'].iteritems(), key=lambda v: (Decimal(v[0]) / 100 + v[1]))[0])),
                ('symbol', materials.Types[k]['symbol']),
                ('rarity', materials.Types[k]['rarity']),
                ('share', OrderedDict(sorted(v['share'].iteritems(), key=lambda v: -Decimal(v[0])))),
            ])
            if 'foundwith' in v:
                fw = v['foundwith']
                ret['foundwith'] = OrderedDict(sorted(fw.iteritems(), key=lambda v: -v[1]))

                if 'foundwithrare' in v:
                    fwr = v['foundwithrare']
                    fwrvals = [(k, fw[k], OrderedDict(sorted(_v.iteritems(), key=lambda v: -v[1]))) for k, _v in fwr.iteritems()]
                    ret['foundwithrare'] = OrderedDict([(k, v) for k, o, v in sorted(fwrvals, key=lambda v: -v[1])])
                    fwr = ret['foundwithrare']
                    ret['foundwithrarerel'] = OrderedDict([(k, OrderedDict([(_k, float(Decimal((_v * 1.0 / fw[k]) / (fw[_k] * 1.0 / count)).quantize(Decimal('1.00')))) for _k, _v in v.iteritems()])) for k, v in fwr.iteritems()])
            if 'byvolcanism' in v:
                ret['byvolcanism'] = OrderedDict(sorted([(k, OrderedDict([
                    ('count', _v['count']),
                    ('mean', float(Decimal(mean(_v['share'])).quantize(Decimal('1.00'))) if _v['share'] else None),
                    ('median', float(median(_v['share'])) if _v['share'] else None),
                    ('mode', float(max(_v['share'].iteritems(), key=lambda v: (Decimal(v[0]) / 100 + v[1]))[0]) if _v['share'] else None),
                    ('share', OrderedDict(sorted(_v['share'].iteritems(), key=lambda v: -Decimal(v[0]))))
                    ])) for k, _v in v['byvolcanism'].iteritems()], key=lambda v: -v[1]['count']))

            return ret
        
        return OrderedDict(sorted([(k, {
            'count': v['count'], 
            'volcanism': OrderedDict(sorted(v['volcanism'].iteritems(), key=lambda v: -v[1])),
            'materials': OrderedDict(sorted([(k, getmatordered(k, v)) for k, v in v['materials'].iteritems()], key=lambda v: -(v[1]['count'] * v[1]['mean'])))
        }) for k, v in bodymatsByType.iteritems()], key=lambda v: -v[1]['count']))

def main():
    print(json.dumps(getmats()))

if __name__ == '__main__':
    main()
