# pixelsaas
Playing with leds

## Prerequisites

This experiment requires Python 2.7 - expect this to increase to target Python 3.4+ at some point. I suggest the use of virtualenvwrapper or just bare virtualenv. These instructions will assume the former.

Finally, git is considered required for getting a copy of the code.

On debian based systems, the following should be enough to install all the initial requirements:

```sudo apt-get install virtualenvwrapper git```

## Installation

If you have not already got a copy of the code, you can clone it from this repo (replace garym with the current fork if appropriate):

```git clone https://github.com/garym/pixelsaas.git```

Make a virtualenv and install the requirements:

```
mkvirtualenv paas
cd pixelsaas
pip install -r requirements.txt
```

Finally install with the following:

```python setup.py develop```

## Running

This program can be thought of as being made up of a number of parts, many of which are available via the ```paas``` program that was installed.

Some programs directly manipulate the pixel display and some only write to a database, requiring the ```paas daemon``` to watch for changes.

An example program is the ```paas gravwell``` which is a very simple simulation of a boardgame by Cryptozoic Entertainment.

Gravwell and Crytozoic Entertainment are trademarks.
