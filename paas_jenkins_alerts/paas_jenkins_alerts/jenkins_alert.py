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

"""A client for watching jenkins jobs."""

import zmq
import json
import time
import jenkins
from paas_common import settings

context = zmq.Context()

sender = context.socket(zmq.REQ)
sender.connect(settings.dataInputPort)

SUCCESS = (0, 0, 255)
WARNING = (255, 106, 0)
ERROR = (255, 0, 0)

alerts = [
    {
        'server_url': 'https://jenkins.example.server',
        'user': 'user',
        'password': 'pass',
        'jobs': [
            {
                'name': 'job1',
            },
            {
                'name': 'job2',
            },
        ],
    },
    {
        'server_url': 'https://jenkins.example2.server',
        'jobs': [
            {
                'name': 'job3',
            },
        ],
    }
]

for alert in alerts:
    url = alert['server_url']
    username = alert.get('user')
    password = alert.get('password')
    server = jenkins.Jenkins(url, username=username, password=password)

    alert['server'] = server


def get_unseen_job_status(server, job):
    jobname = job['name']
    lastSeen = job.get('lastSeen', -1)
    lastComplete = server.get_job_info(jobname)['lastCompletedBuild']['number']
    job['lastSeen'] = lastComplete
    if lastComplete <= lastSeen:
        return job.get('cached_result', None)

    result = server.get_build_info(jobname, lastComplete)['result']
    job['cached_result'] = result
    print('Found new result: {} ({}): {}'.format(jobname, lastComplete, result))
    return result


def send_data(key, rgb):
    data = {
        'topic': 'paas_allpixels',
        'data': {
            'key': "item_{}".format(key),
            'rgb': rgb,
        },
    }
    sender.send_json(json.dumps(data))
    sender.recv_json()


def mainloop():
    while True:
        results = []
        for alert in alerts:
            server = alert['server']
            all_jobs = [j['name'] for j in server.get_jobs()]
            for job in alert['jobs']:
                jobname = job['name']
                if jobname not in all_jobs:
                    continue

                result = get_unseen_job_status(server, job)
                results.append(result == 'SUCCESS')

        rgb = SUCCESS if all(results) else ERROR
        send_data(jobname, rgb)
        time.sleep(15)


def main():
    try:
        mainloop()
    except KeyboardInterrupt:
        print("...\nInterrupt received; cleaning up and exiting.")
    finally:
        sender.close()
        context.term()

if __name__ == '__main__':
    main()
