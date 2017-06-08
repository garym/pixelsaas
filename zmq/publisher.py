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

"""This is the central distribution point of the project. This program acts
as a server to allow clients to input data that will be re-published to any
subscibers to the pubsub socket."""

import os
import os.path
import zmq
import json
import settings

for port in (settings.dataInputPort, settings.pubSubPort):
    if port.startswith('ipc://'):
        portdir = os.path.dirname(port[6:])
        os.makedirs(portdir, exist_ok=True)

context = zmq.Context()

# receiver is the injection point for external data
receiver = context.socket(zmq.REP)
receiver.bind(settings.dataInputPort)

# pubsocket publishes records that are injected to whatever will listen
pubsocket = context.socket(zmq.PUB)
pubsocket.bind(settings.pubSubPort)


def mainloop():
    while True:
        jsondata = receiver.recv_json()
        data = json.loads(jsondata)

        topic = data.get('topic', '')
        message = data.get('data', '')
        pubsocket.send_string("{} {}".format(topic, json.dumps(message)))
        returnmsg = {"message": "Received message on topic '{}'".format(topic)}
        receiver.send_json(json.dumps(returnmsg))

if __name__ == '__main__':
    try:
        mainloop()
    except KeyboardInterrupt:
        print("...\nInterrupt received; cleaning up and exiting.")
    finally:
        pubsocket.close()
        receiver.close()
        context.term()
