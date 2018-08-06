#
# OtterTune - upload.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#
import argparse
import logging
import os
import requests


# Logging
LOG = logging.getLogger(__name__)
LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)


def upload(logfilePath, task_id, url):
    with open(logfilePath, "r+") as logfile:
        lines = logfile.readlines()
        for line in lines:
            if 'Rate limited reqs' in line:
                throughput = line.split(' ')[-2]
                LOG.info("throughput (txn/sec): " + throughput) 

    response = requests.post(url,
                            data={'task_id': task_id,
                                  'throughput': throughput})
                             
    LOG.info(response.content)


def main():
    parser = argparse.ArgumentParser(description="Upload generated data to the website")
    parser.add_argument('logfile', type=str, default='/Users/bohan/Desktop/git/ottertune-web-interface/client/driver/oltp.log', nargs='?',
                        help='OLTPBench log file path')
    parser.add_argument('task_id', type=str, nargs='?', default='1',
                        help='The task id')
    parser.add_argument('url', type=str, default='http://127.0.0.1:8000/new_result/',
                        nargs='?', help='The upload url: server_ip/new_result/')
    args = parser.parse_args()
    upload(args.logfile, args.task_id, args.url)


if __name__ == "__main__":
    main()
