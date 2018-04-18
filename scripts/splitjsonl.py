#!/usr/bin/python3

import json
import sys

ot = None
of = None

for l in sys.stdin:
    if l[0:2] == 'b\'':
        l = eval(l).decode('utf-8')
    j = json.loads(l)
    t = j['header']['gatewayTimestamp'][0:10]
    if of is not None and ot != t:
        of.flush()
        of.close()
        of = None
    if of is None:
        print(t)
        sys.stdout.flush()
        of = open('/srv/eddata/EDDN/{0}.1.jsonl'.format(t), 'a', encoding='utf-8')
        ot = t
    of.write(l)
    of.write('\n')

of.flush()
of.close()
