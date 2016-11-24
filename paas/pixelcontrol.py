#! /usr/bin/env python

#  Copyright 2016 Gary Martin
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

import argparse
import logging
import time
import os

import pickledb
from blinkytape import BlinkyTape, listPorts

from DaemonLite import DaemonLite
import functools
import inotify
import inotify.adapters
import simplejson

logging.basicConfig(level=logging.INFO)
colours = {
    'black': (0.0, 0.0, 0.0),
    'white': (1.0, 1.0, 1.0),
    'red': (1.0, 0.0, 0.0),
    'green': (0.0, 1.0, 0.0),
    'blue': (0.0, 0.0, 1.0),
}

DEF_DBFILE = '/tmp/pixelsaas.db'
LED_COUNT = 60
PIXEL_KEY_FMT = 'pixel_{}'

def process_args():
    ports = listPorts()
    default_port = ports[0] if ports else '/dev/ttyACM0'

    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument('-p', '--port', default=default_port,
                               help='specify the blinkytape port')
    common_parser.add_argument('--max-light-level', default=50, type=int,
                               help='Maximum brightness in range 0 to 255')

    db_parser = argparse.ArgumentParser(add_help=False)
    db_parser.add_argument('-d', '--db-file', default=DEF_DBFILE,
                           help='PickleDB Database file')

    parser = argparse.ArgumentParser(
        description='Pixels as a Service.')

    subparsers = parser.add_subparsers()

    setup_lights_on_parser(subparsers, common_parser)
    setup_lights_off_parser(subparsers, common_parser)
    setup_set_pixel_parser(subparsers, [common_parser, db_parser])
    setup_get_pixel_parser(subparsers, [common_parser, db_parser])
    setup_daemon_parser(subparsers, [common_parser, db_parser]) 

    return parser.parse_args()


def setup_lights_on_parser(subparsers, common_parser):
    parser_on = subparsers.add_parser(
        'on', parents=[common_parser,],
        description='Turn on light.',
        help='Turn on light.'
    )
    parser_on.set_defaults(func=light_on)
    

def light_on(blinky, args):
    c = args.max_light_level
    blinky.displayColor(c, c, c)


def setup_lights_off_parser(subparsers, common_parser):
    parser_off = subparsers.add_parser(
        'off', parents=[common_parser],
        description="Turn off light.",
        help="Turn off data display."
    )
    parser_off.set_defaults(func=light_off)


def light_off(blinky, args):
    blinky.displayColor(0, 0, 0)


def setup_db_conn(db_file):
    return pickledb.load(db_file, True)


def setup_set_pixel_parser(subparsers, parent_parsers):
    parser_set_pixel = subparsers.add_parser(
        'set_pixel', parents=parent_parsers,
        description="Set pixel colour",
        help="Set pixel index to specified colour."
    )
    parser_set_pixel.add_argument('pixel')
    parser_set_pixel.add_argument('colour', nargs=3, type=int)
    parser_set_pixel.set_defaults(func=set_pixel)


def _set_pixel(conn, pixel, colour):
    key = PIXEL_KEY_FMT.format(pixel)
    data = {
        'colour': colour,
        'time': time.time(),
    }
    conn.set(key, data)
    data['id'] = pixel
    return data


def set_pixel(blinky, args):
    db = setup_db_conn(args.db_file)
    _set_pixel(db, args.pixel, args.colour)


def setup_get_pixel_parser(subparsers, parent_parsers):
    parser_get_pixel = subparsers.add_parser(
        'get_pixel', parents=parent_parsers,
        description="Print pixel value.",
        help="Print pixel value."
    )
    parser_get_pixel.add_argument('pixel')
    parser_get_pixel.set_defaults(func=get_pixel)


def _get_pixel(conn, pixel):
    key = PIXEL_KEY_FMT.format(pixel)
    data = conn.get(key)
    if data is None:
        return None
    data['id'] = pixel
    return data


def get_pixel(blinky, args):
    db = setup_db_conn(args.db_file)
    data = _get_pixel(db, args.pixel)
    if data:
        print(data['colour'])
    return data


def _get_pixels(conn):
    return (_get_pixel(conn, i) for i in range(LED_COUNT))


def get_pixels(blinky, args):
    db = setup_db_conn(args.db_file)
    data = [p['colour'] for p in _get_pixels(db)]
    print(data)
    return data


def _delete_pixel(conn, pixel):
    key = PIXEL_KEY_FMT.format(pixel)
    return conn.rem(key)


def display_pixels(blinky, args):
    db = setup_db_conn(args.db_file)
    for i in range(blinky.ledCount):
        data = db.get(PIXEL_KEY_FMT.format(i))
        if data:
            blinky.sendPixel(*data['colour'])
        else:
            blinky.sendPixel(*colours['black'])
    blinky.show()


def touch_file(name):
    with open(name, 'a'):
        os.utime(name, None)


def watch(blinky, args):
    notify = inotify.adapters.Inotify()
    mask = inotify.constants.IN_CLOSE
    notify.add_watch(args.db_file, mask=mask)

    for event in notify.event_gen():
        if event is not None:
            try:
                display_pixels(blinky, args)
            except simplejson.scanner.JSONDecodeError:
                pass


def setup_daemon_parser(subparsers, parent_parsers):
    parser_daemon = subparsers.add_parser(
        'daemon', parents=parent_parsers,
        description="Run daemon to keep pixels up to date.",
        help="Runs program as a daemon to continuously maintain pixel states."
    )
    parser_daemon.add_argument('--pid-file', default='/tmp/pixelsaas.pid',
                           help='PID file for daemon mode')
    parser_daemon.set_defaults(func=daemonise)


def daemonise(blinky, args):
    touch_file(args.db_file)
    class MainDaemon(DaemonLite):
        def run(self):
            watch(blinky, args)

    daemon = MainDaemon(args.pid_file)
    daemon.start()
    #watch(blinky, args)


def set_up_colours(max_value):
    for key, colour in colours.items():
        colours[key] = tuple(int(x * max_value) for x in colour)


def get_blinky_conn(port='/dev/ttyACM0'):
    return BlinkyTape(port)


def main():
    args = process_args()
    blinky = get_blinky_conn(args.port)
    set_up_colours(args.max_light_level)

    args.func(blinky, args)


class PixelDB(object):
    def __init__(self, db_file=DEF_DBFILE):
        self.conn = setup_db_conn(db_file)

    def get_pixel(self, index):
        return _get_pixel(self.conn, index)

    def get_pixels(self):
        return _get_pixels(self.conn)

    def set_pixel(self, index, colour):
        return _set_pixel(self.conn, index, colour)

    def delete_pixel(self, index):
        return _delete_pixel(self.conn, index)

        
if __name__ == '__main__':
    main()
