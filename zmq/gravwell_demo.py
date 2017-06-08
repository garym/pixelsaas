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

"""A simulation of gravwell"""

from itertools import cycle
import json
import settings
import zmq
import random
import time

context = zmq.Context()
sender = context.socket(zmq.REQ)
sender.connect(settings.dataInputPort)

frame_length = 0.2
between_game_frame_length = 5


RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
LIGHT_GREY_001 = (20, 20, 20)
LIGHT_GREY_002 = (40, 40, 40)
LIGHT_GREY_003 = (60, 60, 60)
P1_COLOUR = RED
P2_COLOUR = GREEN
P3_COLOUR = BLUE
P4_COLOUR = YELLOW
JUNK_COLOUR = GREY

LED_COUNT = 64

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

state = {}

BACKGROUND_COLOURS = [BLACK, LIGHT_GREY_001, LIGHT_GREY_002, LIGHT_GREY_002]
gravwell_background = [random.choice(BACKGROUND_COLOURS)
                       for j in range(LED_COUNT)]
gravwell_bg_iter = cycle(gravwell_background)


def reset_state():
    local_state = {
        'player1': {'pos': 0, 'colour': P1_COLOUR},
        'player2': {'pos': 0, 'colour': P2_COLOUR},
        'player3': {'pos': 0, 'colour': P3_COLOUR},
        'player4': {'pos': 0, 'colour': P4_COLOUR},
        'junk1': {'pos': 26, 'colour': JUNK_COLOUR},
        'junk2': {'pos': 36, 'colour': JUNK_COLOUR},
    }

    state.update(local_state)
    random.shuffle(fuel_cards)


def _set_display(pixels):
    pixel_data = {
        {
            'key': "item_{}".format(pixel),
            'rgb': colour,
        }
        for (pixel, colour) in pixels
    }

    data = {
        'topic': 'paas_multipixel',
        'data': {
            'pixels': pixel_data,
            'show': True,
        },
    }
    sender.send_json(json.dumps(data))
    sender.recv_json()


def _set_pixel(pixel, colour):
    data = {
        'topic': 'paas_pixel',
        'data': {
            'key': "item_{}".format(pixel),
            'rgb': colour,
            'show': False,
        },
    }
    sender.send_json(json.dumps(data))
    sender.recv_json()


def _request_display():
    data = {
        'topic': 'paas_showpixels',
        'data': {},
    }
    sender.send_json(json.dumps(data))
    sender.recv_json()


def _blank_out():
    for pos in (range(LED_COUNT)):
        _set_pixel(pos, BLACK)


def _set_background():
    for pos in reversed(range(LED_COUNT)):
        _set_pixel(pos, next(gravwell_bg_iter))
    next(gravwell_bg_iter)


def display_state(state):
    _set_background()
    for player, playerstate in state.items():
        if playerstate['pos'] > -1:
            _set_pixel(LED_COUNT - playerstate['pos'], playerstate['colour'])
    _request_display()


def next_free(state, position, direction):
    for offset in range(LED_COUNT):
        new_position = position + offset * direction
        if not any(p['pos'] == new_position for p in state.values()):
            return new_position


def play_round(state, fuel_cards):
    winner = None
    players = [p for p in state.keys() if p.startswith('p')]

    while winner is None:
        random.shuffle(fuel_cards)
        card_cycler = cycle(fuel_cards)
        for r in range(3):
            # TODO: actual mechanic is for players to select card to play
            #       and order is determined alphabetically
            for player in players:
                # play card
                card = next(card_cycler)
                if card['type'] == 'S':
                    # TODO: determine direction based on nearest player
                    new_position = next_free(
                        state, state[player]['pos'] + card['value'], 1)
                    state[player]['pos'] = new_position
                elif card['type'] == 'R':
                    # TODO: determine direction based on nearest player
                    new_position = next_free(
                        state, state[player]['pos'] - card['value'], -1)
                    state[player]['pos'] = new_position
                else:
                    for opponent in state.keys():
                        # TODO: should be a definite order for this
                        if opponent is not player:
                            if state[opponent]['pos'] > state[player]['pos']:
                                new_position = next_free(
                                    state,
                                    state[opponent]['pos'] - card['value'],
                                    -1)
                            else:
                                new_position = next_free(
                                    state,
                                    state[opponent]['pos'] + card['value'],
                                    1)
                                state[opponent]['pos'] += card['value']
                            state[opponent]['pos'] = new_position

                if state[player]['pos'] >= LED_COUNT:
                    winner = True
                    state[player]['pos'] = LED_COUNT
                if state[player]['pos'] < -1:
                    state[player]['pos'] = -1
                yield state
                if winner:
                    return


def printstate(state):
    entries = reversed(sorted((pstate['pos'], p)
                              for (p, pstate) in state.items()
                              if p.startswith('player')))
    for (score, player) in entries:
        print("{}: {}".format(player, score))


def mainloop():
    _blank_out()
    while True:
        reset_state()
        display_state(state)

        for step_state in play_round(state, fuel_cards):
            display_state(step_state)
            time.sleep(frame_length)

        print("Finished")
        printstate(step_state)
        time.sleep(between_game_frame_length)

if __name__ == '__main__':
    try:
        mainloop()
    except KeyboardInterrupt:
        print("...\nInterrupt received; cleaning up and exiting.")
    finally:
        sender.close()
        context.term()
