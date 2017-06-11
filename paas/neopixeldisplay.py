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

"""This is the display code for the unicornhat output.

It subscribes to the 'pixel' topic of the publisher and will display
anything that has valid json in the form

  {'key': 'abc', 'rgb': [1, 2, 3]}

Note that this is not necessarily directly related to how the data
should be structured for input to the publisher - this is only what
the publisher should provide that this subscriber will understand.

This modules is expected to be run directly as its own process. The
requirements of the unicornhat are such that you are expected to run
code for interacting with it as root (or with sudo). The ability to
run this relatively small part of the program should reduce the risk
associated with this.
"""


import json
import random
import sys
import zmq
import settings
import unicornhat as unicorn


unicorn.set_layout(unicorn.AUTO)
unicorn.rotation(0)
unicorn.brightness(1)

WIDTH, HEIGHT = unicorn.get_shape()
keymap = {}
all_positions = set((i, j) for i in range(WIDTH) for j in range(HEIGHT))

context = zmq.Context()
subsocket = context.socket(zmq.SUB)
subsocket.connect(settings.pubSubPort)

topic_filter = sys.argv[1] if len(sys.argv) > 1 else "paas_"

if isinstance(topic_filter, bytes):
    topic_filter = topic_filter.decode('ascii')
subsocket.setsockopt_string(zmq.SUBSCRIBE, topic_filter)

try:
    ALLOCATION_SCHEME = settings.pixel_allocation_scheme
except AttributeError:
    ALLOCATION_SCHEME = 'linear'


def get_position_for_key(key):
    if key in keymap:
        return keymap[key]

    positions = all_positions - set(keymap.values())
    if not positions:
        return (0, 0)

    if ALLOCATION_SCHEME == 'random':
        position = random.choice(list(positions))
    else:
        position = sorted(list(positions))[-1]
    keymap[key] = position
    return position


def set_pixel(data):
    key = data.get('key', None)
    x, y = get_position_for_key(key)
    r, g, b = data.get('rgb', (None, None, None))
    unicorn.set_pixel(x, y, r, g, b)


def set_all_pixels(data):
    r, g, b = data.get('rgb', (None, None, None))
    unicorn.set_all(r, g, b)


def mainloop():
    while True:
        response = subsocket.recv_string()
        topic, *splitdata = response.split()
        data = json.loads(' '.join(splitdata))
        if topic == 'paas_pixel':
            set_pixel(data)
        elif topic == 'paas_allpixels':
            set_all_pixels(data)

        if topic == 'paas_showpixels' or data.get('show', True):
            unicorn.show()


if __name__ == '__main__':
    try:
        mainloop()
    except KeyboardInterrupt:
        print("...\nInterrupt received; cleaning up and exiting.")
    finally:
        subsocket.close()
        context.term()
