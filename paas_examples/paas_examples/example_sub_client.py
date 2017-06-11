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

"""A simple subscriber to the main publisher."""

import sys
import zmq
import json
from paas_common import settings

context = zmq.Context()

listener = context.socket(zmq.SUB)
listener.connect(settings.pubSubPort)
listener.setsockopt(zmq.SUBSCRIBE, b'pixel')

while True:
    data = listener.recv()

    print("received:" , data)
