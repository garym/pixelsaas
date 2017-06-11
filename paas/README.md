# pixelsaas
Playing with leds and zeromq

## Prerequisites

Python 3.4+

I recommend the use of virtualenvwrapper or just bare virtualenv. These
instructions will assume the former.

If you are running linux and want to play with any code that requires the use
of credentials (e.g. the jenkins monitor for), you will probably also need to
install the python3-dbus system package for this to work and setup your
virtualenv a little differently.

Finally, git is considered required for getting a copy of the code.

On fedora based systems, the following should be enough to install all the
initial requirements:

```sudo dnf install virtualenvwrapper git python3-dbus```

## Installation

If you have not already got a copy of the code, you can clone it from this
repo (replace garym with the current fork if appropriate):

```git clone https://github.com/garym/pixelsaas.git```

Make a virtualenv and install the requirements:

```
mkvirtualenv -p python3 --system-site-packages paas
cd pixelsaas/zmq
pip install -r requirements.txt
```

## Running

The program is currently made up of a number of scripts that are intended to
be run separately. These are roughly divided into:

 * Core:
   * publisher.py
 * Data Consumers:
   * database.py
   * neopixeldisplay.py
 * Data Creation Clients:
   * example_data_client.py
   * gravwell_demo.py

Due to the nature of the underlying architecture, new consumers and clients
may start to use multiple programs.

The clients, core and consumers form a pipeline which can in principle be
branched in many ways, depending on what is required. The core publisher is
the central point of the program and so it would normally be expected to be
running regardless. It currently runs as a server listening on a socket
and it will publish messages over a pubsub socket.

At the moment the only working data consumer is the neopixel display script.
It is designed to connect to the pubsub and listen for certain topics that
it understands and respond by updating the pixels displayed.

The database consumer should eventually be a place where, if desired, the
messages coming over the pubsub socket will be injested. The idea with this
is that it could act as a place to replay the events for services that need
to learn state that they may have missed.

Further backends are intended to be created.

The clients are then effectively either demo programs or actual interesting
use cases for the system.

The gravwell_demo.py program is a very simple simulation of a boardgame by
Cryptozoic Entertainment called Gravwell. Not all of the rules associated
with the game are properly implemented but it works as a set of simulated
players blindly playing cards. (Gravwell and Crytozoic Entertainment are
trademarks.)

The example_data_client.py goes through a number of cycles of generating
random colours to be displayed followed by sequential full display colour
display requests.

It should be noted that the clients at this point are required to be fairly
aware of what the neopixeldisplay.py program requires to display.

Connecting up the system is currently acheived to an extent by a shared
settings.py file - this can also be expected to change so that settings are
properly localised and should not get put in source control. The scripts
can start in any order though if you want to get the best out of it, you
may want to start consumers prior to any clients being able to send their
data through the publisher. The clients will block patiently until there is
a server to accept their input.
