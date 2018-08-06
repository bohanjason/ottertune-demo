#
# OtterTune - fabfile.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#
'''
Created on Mar 23, 2018

@author: bohan
'''
import sys
import json
import logging
import time
import os.path
import re
from multiprocessing import Process
from fabric.api import (env, local, task, lcd)
from fabric.state import output as fabric_output

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)
Formatter = logging.Formatter("%(asctime)s [%(levelname)s]  %(message)s")  # pylint: disable=invalid-name

# print the log
ConsoleHandler = logging.StreamHandler(sys.stdout)  # pylint: disable=invalid-name
ConsoleHandler.setFormatter(Formatter)
LOG.addHandler(ConsoleHandler)

# Fabric environment settings
env.hosts = ['localhost']
fabric_output.update({
    'running': True,
    'stdout': True,
})

with open('driver_config.json', 'r') as f:
    CONF = json.load(f)


@task
def check_disk_usage():
    partition = CONF['database_disk']
    disk_use = 0
    cmd = "df -h {}".format(partition)
    out = local(cmd, capture=True).splitlines()[1]
    m = re.search('\d+(?=%)', out)  # pylint: disable=anomalous-backslash-in-string
    if m:
        disk_use = int(m.group(0))
    LOG.info("Current Disk Usage: %s%s", disk_use, '%')
    return disk_use


@task
def restart_database():
    if CONF['database_type'] == 'postgres':
        cmd = 'brew services restart postgres' #ubuntu: 'sudo service postgresql restart'
    else:
        raise Exception("Database Type {} Not Implemented !".format(CONF['database_type']))
    local(cmd)


@task
def drop_database():
    if CONF['database_type'] == 'postgres':
        cmd = "PGPASSWORD={} dropdb -e --if-exists {} -U {}".\
              format(CONF['password'], CONF['database_name'], CONF['username'])
    else:
        raise Exception("Database Type {} Not Implemented !".format(CONF['database_type']))
    local(cmd)


@task
def create_database():
    if CONF['database_type'] == 'postgres':
        cmd = "PGPASSWORD={} createdb -e {} -U {}".\
              format(CONF['password'], CONF['database_name'], CONF['username'])
    else:
        raise Exception("Database Type {} Not Implemented !".format(CONF['database_type']))
    local(cmd)


@task
def change_conf(task_id=1):
    next_conf = 'config_{}'.format(task_id)
    if CONF['database_type'] == 'postgres':
        cmd = 'sudo python PostgresConf.py {} {}'.format(next_conf, CONF['database_conf'])
    else:
        raise Exception("Database Type {} Not Implemented !".format(CONF['database_type']))
    local(cmd)


@task
def load_oltpbench():
    cmd = "./oltpbenchmark -b {} -c {} --create=true --load=true".\
          format(CONF['oltpbench_workload'], CONF['oltpbench_config'])
    with lcd(CONF['oltpbench_home']):  # pylint: disable=not-context-manager
        local(cmd)

@task
def run_oltpbench():
    cmd = "./oltpbenchmark -b {} -c {} --execute=true -s 5 -o outputfile > {} ".\
          format(CONF['oltpbench_workload'], CONF['oltpbench_config'], CONF['oltpbench_log'])
    with lcd(CONF['oltpbench_home']):  # pylint: disable=not-context-manager
        local(cmd)

@task
def save_dbms_result(task_id=1):
    cmd_conf = 'mv ./config_{} {}'.format(task_id, CONF['save_path'])
    cmd_oltpbench = 'cp {} {}/result_{}'.format(CONF['oltpbench_log'], CONF['save_path'], task_id)
    local(cmd_conf)
    local(cmd_oltpbench)



@task
def free_cache():
    cmd = 'sync; sudo bash -c "echo 1 > /proc/sys/vm/drop_caches"'
    local(cmd)


@task
def upload_result(task_id=1):
    cmd = 'python ./upload.py {} {} {}'.format(CONF['oltpbench_log'],
                                               task_id,
                                               "http://127.0.0.1:8000/new_result/")
    local(cmd)


@task
def get_result(task_id=1):
    cmd = 'python ../../script/get_result.py http://127.0.0.1:8000 {} 5'.\
          format(task_id)
    local(cmd)

@task
def loop(task_id=1):

    # free cache
    # free_cache()

    # get result
    get_result(task_id)

    # change config
    change_conf(task_id)

    # restart database
    restart_database()

    # run oltpbench
    run_oltpbench()

    # upload result
    upload_result(task_id)

    # move config 
    save_dbms_result(task_id)


@task
def run_loops(max_iter=1):
    for i in range(int(max_iter)):
        LOG.info('The %s-th Loop Starts / Total Loops %s', i + 1, max_iter)
        loop(i + 1)
        LOG.info('The %s-th Loop Ends / Total Loops %s', i + 1, max_iter)
