#!/usr/bin/env python

#  Copyright 2017 Gary Martin
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""This process listens on the pubsub socket and will put data it
subscribes to into the database"""

import zmq
import json
import settings
import pickledb

context = zmq.Context()
subsocket = context.socket(zmq.SUB)
subsocket.connect(settings.pubSubPort)
subsocket.setsockopt_string(zmq.SUBSCRIBE, u'pixel')

servsocket = context.socket(zmq.REP)
servsocket.bind(settings.dbPort)

poller = zmq.Poller()
poller.register(subsocket, zmq.POLLIN)
poller.register(servsocket, zmq.POLLIN)

dbconn = pickledb.load(settings.dbFile, True)


def retrieve_data(key):
    return json.dumps(dbconn.get(key))


def store_record():
    response = subsocket.recv_string()
    topic, *splitdata = response.split()
    data = json.loads(' '.join(splitdata))
    key = data.get('key', None)
    if key is not None:
        dbconn.set(key, data)


def mainloop():
    while True:
        socks = dict(poller.poll())
        if subsocket in socks:
            store_record()

        if servsocket in socks:
            data = retrieve_data(servsocket.recv())
            servsocket.send(data)

if __name__ == '__main__':
    try:
        mainloop()
    except KeyboardInterrupt:
        print("...\nInterrupt received; cleaning up and exiting.")
    finally:
        subsocket.close()
        servsocket.close()
        context.term()
