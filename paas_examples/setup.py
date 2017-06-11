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
    name='paas_examples',
    version='0.2.0-SNAPSHOT',
    description='Provides example programs for inputs to paas.',
    author='Gary Martin',
    author_email='gary.martin@physics.org',
    url='https://github.com/garym/PixelsAAS',
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'paas_gravwell_demo=paas_examples.gravwell_demo:main',
            'paas_example_data_demo=paas_examples.example_data_client:main',
        ],
    },
    packages=(
        'paas_examples',
    ),
)
