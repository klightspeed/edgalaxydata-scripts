#!/usr/bin/python3

import zlib
import zmq
import json
import sys
import time
from datetime import datetime
#import mysql.connector

relay = 'tcp://eddn.edcd.io:9500'
timeout = 600000

outfiles = {}
outfilenames = {}
anonfiles = {}
anonfilenames = {}

message_types = {
    'https://eddn.edcd.io/schemas/journal/1': 'Journal',
    'https://eddn.edcd.io/schemas/outfitting/2': 'Outfitting',
    'https://eddn.edcd.io/schemas/shipyard/2': 'Shipyard',
    'https://eddn.edcd.io/schemas/commodity/3': 'Commodity',
    'https://eddn.edcd.io/schemas/blackmarket/1': 'BlackMarket',
    'https://eddn.edcd.io/schemas/journal/1/test': 'Test-Journal',
    'https://eddn.edcd.io/schemas/outfitting/2/test': 'Test-Outfitting',
    'https://eddn.edcd.io/schemas/shipyard/2/test': 'Test-Shipyard',
    'https://eddn.edcd.io/schemas/commodity/3/test': 'Test-Commodity',
    'https://eddn.edcd.io/schemas/blackmarket/1/test': 'Test-BlackMarket',
}

eddndir = '/srv/eddata/EDDN'
anondir = '/srv/eddata/EDDN-anon'

def process_msg(msgtype, msg, msgraw):
    global outfiles
    global outfilenames
    global anonfiles
    global anonfilenames
    print(msgraw.decode('utf-8'))
    sys.stdout.flush()
    date = datetime.utcnow()
    if msgtype in ['Journal', 'Test-Journal']:
        eventtype = msgtype + '.' + msg['message']['event']
    else:
        eventtype = msgtype
    filename = eddndir + '/{0}-{1:%Y-%m-%d}.jsonl'.format(eventtype, date)
    anonname = anondir + '/{0}-{1:%Y-%m-%d}.jsonl'.format(eventtype, date)
    if eventtype in outfiles and outfiles[eventtype] is not None and outfilenames[eventtype] != filename:
        outfiles[eventtype].close()
        outfiles[eventtype] = None
    if eventtype in anonfiles and anonfiles[eventtype] is not None and anonfilenames[eventtype] != anonname:
        anonfiles[eventtype].close()
        anonfiles[eventtype] = None
    if eventtype not in outfiles or outfiles[eventtype] is None:
        outfilenames[eventtype] = filename
        outfiles[eventtype] = open(outfilenames[eventtype], 'a', encoding='utf-8')
    if eventtype not in anonfiles or anonfiles[eventtype] is None:
        anonfilenames[eventtype] = anonname
        anonfiles[eventtype] = open(anonfilenames[eventtype], 'a', encoding='utf-8')
    outfiles[eventtype].write(msgraw.decode('utf-8'))
    outfiles[eventtype].write('\n')
    outfiles[eventtype].flush()
    anonfiles[eventtype].write(json.dumps(msg, sort_keys=True))
    anonfiles[eventtype].write('\n')
    anonfiles[eventtype].flush()

def main():
    context = zmq.Context()
    subscriber = context.socket(zmq.SUB)
    subscriber.setsockopt(zmq.SUBSCRIBE, b'')
    subscriber.setsockopt(zmq.RCVTIMEO, timeout)

    while True:
        try:
            subscriber.connect(relay)

            while True:
                message = subscriber.recv()

                if message == False:
                    subscriber.disconnect(relay)
                    break

                message = zlib.decompress(message)
                msg = json.loads(message.decode('utf-8'))
                msgtype = msg['$schemaRef']
                if msgtype in message_types:
                    msgtype = message_types[msgtype]
                    del msg['header']['uploaderID']
                    try:
                        process_msg(msgtype, msg, message)
                    except AttributeError:
                        print('Unhandled event: {0}'.format(json.dumps(msg)))

        except zmq.ZMQError as e:
            sys.stderr.write('ZMQ Error: {0}\n'.format(e))
            sys.stderr.flush()
            subscriber.disconnect(relay)
            time.sleep(5)

if __name__ == '__main__':
    main()

                
