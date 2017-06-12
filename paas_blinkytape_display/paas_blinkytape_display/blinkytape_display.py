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

"""This is the display code for the blinkytape output.

It subscribes to the 'pixel' topic of the publisher and will display
anything that has valid json in the form

  {'key': 'abc', 'rgb': [1, 2, 3]}

Note that this is not necessarily directly related to how the data
should be structured for input to the publisher - this is only what
the publisher should provide that this subscriber will understand.

This modules is expected to be run directly as its own process.
"""


import json
import random
import sys
import zmq
from blinkytape import BlinkyTape, listPorts
from paas_common import settings

port = listPorts()[0]
blinky = BlinkyTape(port)

keymap = {}
all_positions = set(i for i in range(blinky.ledCount))

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

pixel_values = [(0, 0, 0)] * blinky.ledCount


def set_pixel(data):
    key = data.get('key', None)
    i = get_position_for_key(key)
    r, g, b = data.get('rgb', (None, None, None))
    pixel_values[i] = (r, g, b)


def set_all_pixels(data):
    r, g, b = data.get('rgb', (0, 0, 0))
    for p in range(len(pixel_values)):
        pixel_values[p] = (r, g, b)


def update_display():
    for p in pixel_values:
        blinky.sendPixel(p)
    blinky.show()


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
            update_display()


def main():
    try:
        mainloop()
    except KeyboardInterrupt:
        print("...\nInterrupt received; cleaning up and exiting.")
    finally:
        subsocket.close()
        context.term()

if __name__ == '__main__':
    main()
