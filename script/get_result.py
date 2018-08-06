#
# OtterTune - query_and_get.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#
'''
Created on Feb 11, 2018
@author: taodai
'''

import urllib
import sys
import time
import logging
import json

# Logging
LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)


# take 3 arguments, save result to next_config in working directory
# base_url: for instance, https://0.0.0.0:8000/
# task_id: task id...
# query_interval: time (in second) between queries
def main():
    base_url = sys.argv[1].strip('/')
    task_id = sys.argv[2]
    query_interval = int(sys.argv[3])
    request = base_url + '/get_result/' + task_id
    timer = 0
    start = time.time()
    while True:
        response = urllib.urlopen(request).read().decode()
        if 'Fail' in response:
            LOG.info('Tuning failed\n')
            break
        elif 'Invalid task id' in response:
            time.sleep(query_interval)
            timer += query_interval
            LOG.info('%s s', str(timer))
        else:
            next_conf_f = open('config_{}'.format(task_id), 'w')
            knob_settings = json.loads(response)
            ret = {}
            ret["task_id"] = task_id
            ret["recommendation"] = knob_settings
            next_conf_f.write(json.dumps(ret))
            next_conf_f.close()
            print knob_settings
            break

    elapsed_time = time.time() - start
    LOG.info('Elapsed time: %s\n', str(elapsed_time))
    return knob_settings

if __name__ == "__main__":
    main()