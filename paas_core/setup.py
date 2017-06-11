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

from setuptools import setup


requires = (
    'pyzmq',
    'paas-common===0.2.0-SNAPSHOT',
)

setup(
    name='paas_core',
    version='0.2.0-SNAPSHOT',
    description='Provides core message injection point and pubsub for paas.',
    author='Gary Martin',
    author_email='gary.martin@physics.org',
    url='https://github.com/garym/PixelsAAS',
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'paas_core=paas_core.core:main',
        ],
    },
    packages=(
        'paas_core',
    ),
)
