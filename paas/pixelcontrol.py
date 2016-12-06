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
from itertools import cycle
import logging
import random
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

RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (63, 63, 63)
LIGHT_GREY_001 = (1, 1, 1)
LIGHT_GREY_002 = (2, 2, 2)
LIGHT_GREY_003 = (3, 3, 3)
P1_COLOUR = RED
P2_COLOUR = GREEN
P3_COLOUR = BLUE
P4_COLOUR = YELLOW
JUNK_COLOUR = GREY

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
    setup_gravwell_parser(subparsers, [common_parser, db_parser])
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


def setup_gravwell_parser(subparsers, parent_parsers):
    parser_gravwell = subparsers.add_parser(
        'gravwell', parents=parent_parsers,
        description='Run gravwell demo.',
        help='Run gravwell demo.'
    )
    parser_gravwell.add_argument('--forever', default=False,
                                 action="store_true",
                                 help='keep on going')
    parser_gravwell.add_argument('--frame-length', default=0.25, type=float,
                                 help='Length of a frame in seconds.')
    parser_gravwell.add_argument('--frames-per-step', default=4, type=int,
                                 help='Number of frames per simulation step.')
    parser_gravwell.set_defaults(func=gravwell_demo)


BACKGROUND_COLOURS = [BLACK, LIGHT_GREY_001, LIGHT_GREY_002, LIGHT_GREY_002]
gravwell_background = [random.choice(BACKGROUND_COLOURS) for j in range(LED_COUNT)]
gravwell_bg_iter = cycle(gravwell_background)

def _set_background(db):
    for pos in reversed(range(LED_COUNT)):
        _set_pixel(db, pos, gravwell_bg_iter.next())
    gravwell_bg_iter.next()


def display_state(db, state):
    _set_background(db)
    for player, playerstate in state.items():
        if playerstate['pos'] > -1:
            _set_pixel(db, 60 - playerstate['pos'], playerstate['colour'])


def gravwell_demo(blinky, args):
    # initialisation
    db = setup_db_conn(args.db_file)

    frame_length = args.frame_length
    frames_per_step = args.frames_per_step

    # game state
    while True:
        state = {
            'player1': {'pos': 0, 'colour': P1_COLOUR},
            'player2': {'pos': 0, 'colour': P2_COLOUR},
            'player3': {'pos': 0, 'colour': P3_COLOUR},
            'player4': {'pos': 0, 'colour': P4_COLOUR},
            'junk1': {'pos': 26, 'colour': JUNK_COLOUR},
            'junk2': {'pos': 36, 'colour': JUNK_COLOUR},
        }

        fuel_cards = [
            {'name': 'Ar', 'value': 1, 'type': 'S'},
            {'name': 'B', 'value': 2, 'type': 'S'},
            {'name': 'C', 'value': 3, 'type': 'S'},
            {'name': 'Dy', 'value': 5, 'type': 'S'},
            {'name': 'Es', 'value': 2, 'type': 'S'},
            {'name': 'F', 'value': 6, 'type': 'S'},
            {'name': 'G', 'value': 5, 'type': 'S'},
            {'name': 'H', 'value': 4, 'type': 'S'},
            {'name': 'Ir', 'value': 6, 'type': 'S'},
            {'name': 'Ja', 'value': 2, 'type': 'TB'},
            {'name': 'Kr', 'value': 2, 'type': 'R'},
            {'name': 'L', 'value': 4, 'type': 'S'},
            {'name': 'Mg', 'value': 10, 'type': 'S'},
            {'name': 'Ne', 'value': 6, 'type': 'R'},
            {'name': 'O', 'value': 7, 'type': 'S'},
            {'name': 'Pu', 'value': 5, 'type': 'S'},
            {'name': 'Q', 'value': 3, 'type': 'TB'},
            {'name': 'Ra', 'value': 9, 'type': 'S'},
            {'name': 'S', 'value': 9, 'type': 'S'},
            {'name': 'Th', 'value': 2, 'type': 'S'},
            {'name': 'U', 'value': 5, 'type': 'R'},
            {'name': 'V', 'value': 7, 'type': 'S'},
            {'name': 'W', 'value': 8, 'type': 'S'},
            {'name': 'Xe', 'value': 3, 'type': 'R'},
            {'name': 'Yr', 'value': 8, 'type': 'S'},
            {'name': 'Zr', 'value': 7, 'type': 'S'},
        ]

        random.shuffle(fuel_cards)
        display_state(db, state)

        for step_state in play_round(db, state, fuel_cards):
            for i in range(frames_per_step):
                display_state(db, step_state)
                time.sleep(frame_length)

        print("Finished")
        if not args.forever:
            return
        for i in range(300):
            display_state(db, state)
            time.sleep(frame_length)


def next_free(db, state, position, direction):
    for offset in range(LED_COUNT):
        new_position = position + offset * direction
        if not any(p['pos'] == new_position for p in state.values()):
            return new_position


def play_round(db, state, fuel_cards):
    winner = None
    players = [p for p in state.keys() if p.startswith('p')]

    while winner is None:
        random.shuffle(fuel_cards)
        card_cycler = cycle(fuel_cards)
        for r in range(3):
            # TODO: actual mechanic is for players to select card to play and order is
            #       determined alphabetically
            for player in players:
                # play card
                card = card_cycler.next()
                if card['type'] == 'S':
                    # TODO: determine direction based on nearest player
                    new_position = next_free(db, state, state[player]['pos'] + card['value'], 1)
                    state[player]['pos'] = new_position
                elif card['type'] == 'R':
                    # TODO: determine direction based on nearest player
                    new_position = next_free(db, state, state[player]['pos'] - card['value'], -1)
                    state[player]['pos'] = new_position
                else:
                    for opponent in state.keys():
                        # TODO: should be a definite order for this
                        if opponent is not player:
                            if state[opponent]['pos'] > state[player]['pos']:
                                new_position = next_free(db, state, state[opponent]['pos'] - card['value'], -1)
                            else:
                                new_position = next_free(db, state, state[opponent]['pos'] + card['value'], 1)
                                state[opponent]['pos'] += card['value']
                            state[opponent]['pos'] = new_position

                if state[player]['pos'] >= 59:
                    winner = True
                    state[player]['pos'] = 59
                if state[player]['pos'] < -1:
                    state[player]['pos'] = -1
                yield state
                if winner:
                    return


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
