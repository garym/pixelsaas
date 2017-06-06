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

"""A simple client for inputting test data that will eventually make it
through to the display. This inputs data on the publisher as a REQ socket
in the hope that it will get published in the appropriate form for the
display.
"""

import sys
import zmq
import json
import settings
import random
import time
import itertools

context = zmq.Context()

sender = context.socket(zmq.REQ)
sender.connect(settings.dataInputPort)

GOOD = (0, 0, 255)
WARNING = (255, 106, 0)
ERROR = (255, 0, 0)

for j in range(1000):
    for i in range(64):
        rgb = random.choice((GOOD, WARNING, ERROR))
        data = {
            'topic': 'paas_pixel',
            'data': {
                'key': "item_{}".format(i),
                'rgb': rgb,
            },
        }
        sender.send_json(json.dumps(data))
        response = sender.recv_json()

for i, status in enumerate(itertools.cycle((GOOD, WARNING, ERROR))):
    if i > 100:
        break
    data = {
        'topic': 'paas_allpixels',
        'data': {
            'key': "item_{}".format(i),
            'rgb': status,
        },
    }
    sender.send_json(json.dumps(data))
    response = sender.recv_json()
    time.sleep(1)
