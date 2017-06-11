# pixelsaas
Playing with leds and zeromq

## Prerequisites

Python 3.4+

I recommend the use of virtualenvwrapper or just bare virtualenv. These
instructions will assume the former.

Finally, git is considered required for getting a copy of the code.

On fedora based systems, the following should be enough to install all the
initial requirements:

```sudo dnf install virtualenvwrapper git```

## Installation Preparation

If you have not already got a copy of the code, you can clone it from this
repo (replace garym with the current fork if appropriate):

```
git clone https://github.com/garym/pixelsaas.git
cd pixelsaas
```

Make a virtualenv:

```
mkvirtualenv -p python3 --system-site-packages paas
```

## Installation Paths

From this point, the installation path in part depends on what parts you
want to run. Some components may not be installable on all platforms and
due to the nature of the project, it is possible to install components on
different servers and everything should still work with proper settings.


### All Components on Raspberry Pi:

If you are interested in running all the components on a Raspberry Pi then
you can run:

```
pip install -r requirements_rpi_all.txt
```

### Individual components:

All the components rely on paas_common:

```
pip install paas_common/
```

The install the components you want, e.g.:

```
pip install paas_examples/
pip install paas_core/
pip install paas_unicornhat_display/
```

## Running

Running paas is about running a set of separate scripts that communicate via
sockets. The installed scripts can be run independently in any order though
you may wish to start the display ahead of starting the core.


 * Core:
   * `paas_core`
 * Data Consumers:
   * `paas_unicornhat`
 * Data Creation Clients:
   * `paas_example_data_demo`
   * `paas_gravwell_demo`

The clients, core and consumers form a pipeline which can in principle be
branched in many ways, depending on what is required. The `paas_core`
publisher is the central point of the program and so it would normally be
expected to be running regardless. It currently runs as a server listening on
a socket and it will publish messages over a pubsub socket.

At the moment the only working data consumer is the `paas_unicornhat` display
script. It is designed to connect to the core pubsub socket and listen for
certain topics that it understands and respond by updating the pixels
displayed.

A database consumer should eventually be a place where, if desired, messages
coming over the pubsub socket will be injested. The idea with this is that it
could act as a place to replay the events for services that need to learn
state that they may have missed.

Further consumer backends are intended to be created, in particular for more
display options.

The clients are then effectively either demo programs or actual interesting
use cases for the system.

The `paas_gravwell_demo` program is a very simple simulation of a boardgame
by Cryptozoic Entertainment called Gravwell. Not all of the rules associated
with the game are properly implemented but it works as a set of simulated
players blindly playing cards. (Gravwell and Crytozoic Entertainment are
trademarks.)

The `paas_example_data_demo` goes through a number of cycles of generating
random colours to be displayed followed by sequential full display colour
display requests.

It should be noted that the clients at this point are required to be fairly
aware of what displays programs require for display.

Connecting up the system is currently acheived to an extent by a shared
settings.py file - this can also be expected to change so that settings are
properly localised and should not get put in source control. The scripts
can start in any order though if you want to get the best out of it, you
may want to start consumers prior to any clients being able to send their
data through the publisher. The clients will block patiently until there is
a server to accept their input.
