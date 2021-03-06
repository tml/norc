#!/usr/bin/python

import sys
import random, string
import datetime
from norc.core.models import *

def random_string(a, b=None):
    CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890_'
    length = random.randint(a, b) if b else a
    return "".join([random.choice(CHARS) for _ in range(length)])
    
HOSTS = ['.'.join([random_string(3) for _ in range(3)]) for _ in range(20)]

def choice_from_queryset(q):
    return q[random.randint(0, len(q) - 1)]

def print_period():
    sys.stdout.write('.')
    sys.stdout.flush()

def add_region():
    ResourceRegion(name=random_string(10,20)).save()

def add_daemon():
    region = choice_from_queryset(ResourceRegion.objects.all())
    global HOSTS
    host = random.choice(HOSTS)
    pid = random.randint(15000, 25000)
    r = random.random()
    if r < 0.85:
        status = NorcDaemonStatus.STATUS_ENDEDGRACEFULLY
    elif r < 0.9:
        status = NorcDaemonStatus.STATUS_ERROR
    elif r < 0.95:
        status = NorcDaemonStatus.STATUS_RUNNING
    else:
        status = random.choice(NorcDaemonStatus.ALL_STATUSES)
    started = datetime.datetime.now() - datetime.timedelta(
        seconds=random.randrange(1209600))
    if status in [NorcDaemonStatus.STATUS_ERROR,
                  NorcDaemonStatus.STATUS_PAUSED,
                  NorcDaemonStatus.STATUS_ENDEDGRACEFULLY,
                  NorcDaemonStatus.STATUS_KILLED,
                  NorcDaemonStatus.STATUS_DELETED]:
        ended = started + datetime.timedelta(
            seconds=random.uniform(120, 60*60*24))
    else:
        ended = None
    NorcDaemonStatus(region=region, host=host, pid=pid, status=status,
        date_started=started, date_ended=ended).save()

def add_job():
    job = Job(name=random_string(5,15), description=random_string(20, 30))
    job.save()
    for _ in range(random.randint(1, 10)):
        add_iteration(job)
    print_period()
    for _ in range(random.randint(0, 20)):
        add_task(job)

def add_iteration(job):
    status = random.choice(Iteration.ALL_STATUSES)
    type_ = random.choice(Iteration.ALL_ITER_TYPES)
    started = datetime.datetime.now() - datetime.timedelta(
        seconds=random.randrange(1209600))
    if type_ == Iteration.ITER_TYPE_EPHEMERAL:
        ended = started + datetime.timedelta(
            seconds=random.uniform(30, 60*60))
    else:
        ended = None
    Iteration(job=job, iteration_type=type_, status=status,
        date_started=started, date_ended=ended).save()

def add_task(job):
    r = random.random()
    if r < 0.9:
        status = Task.STATUS_ACTIVE
    else:
        status = random.choice(Task.ALL_STATUSES)
    rc = RunCommand(job=job, status=status, cmd='', timeout=300)
    rc.save()
    iterations = list(job.iteration_set.all())
    daemons = list(NorcDaemonStatus.objects.all())
    for _ in xrange(random.randint(0, 500)):
        iteration = random.choice(iterations)
        daemon = random.choice(daemons)
        add_trs(rc, iteration, daemon)
    print_period()

def add_trs(task, iteration, daemon):
    r = random.random()
    if r < 0.8:
        status = TaskRunStatus.STATUS_SUCCESS
    elif r < 0.9:
        status = TaskRunStatus.STATUS_ERROR
    else:
        status = random.choice(TaskRunStatus.ALL_STATUSES)
    started = iteration.date_started + datetime.timedelta(
        seconds=random.uniform(30, 60*60))
    if status != TaskRunStatus.STATUS_RUNNING:
        ended = started + datetime.timedelta(seconds=random.uniform(0.1, 5))
    else:
        ended = None
    trs = TaskRunStatus(task=task, iteration=iteration, status=status,
        date_started=started, date_ended=ended, controlling_daemon=daemon)
    trs.save()

def populate():
    for _ in range(10):
        add_region()
    print_period()
    for _ in range(random.randint(500, 1000)):
        add_daemon()
    print_period()
    for _ in range(10):
        add_job()
    print ''

if __name__ == '__main__':
    populate()
