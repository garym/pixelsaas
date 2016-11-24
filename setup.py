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

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


requires = (
    'BlinkyTape',
    'pyserial',
)
versions = (
    '0.1.0',
)

setup(
    name='PixelsAAS',
    version=versions[-1],
    description='Providing pixels as a service',
    author='Gary Martin',
    author_email='gary.martin@physics.org',
    url='https://github.com/garym/PixelsAAS',
    requires=requires,
    entry_points={
        'console_scripts': [
            'paas=paas.pixelcontrol:main',
        ],
    },
)
