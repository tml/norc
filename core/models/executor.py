
"""The Norc Executor (norcd) is defined here."""

import os
import sys
import signal
import time
from datetime import datetime, timedelta
from threading import Thread, Event
# from multiprocessing import Process
# Alas, 2.5 doesn't have multiprocessing...
from subprocess import Popen

from django.db.models import (Model, Manager, query,
    CharField,
    DateTimeField,
    IntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    ForeignKey)
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import (GenericRelation,
                                                 GenericForeignKey)

from norc.core.models.queue import Queue
from norc.core.constants import (Status,
    CONCURRENCY_LIMIT, HEARTBEAT_PERIOD, HEARTBEAT_FAILED, INSTANCE_MODELS)
from norc.norc_utils.django_extras import QuerySetManager, MultiQuerySet
from norc.norc_utils.parallel import ThreadPool
from norc.norc_utils.log import make_log
from norc.norc_utils.backup import backup_log
from norc import settings

class Executor(Daemon):
    """Executors are responsible for the running of instances.
    
    Executors have a single queue that they pull instances from.  There
    can (and in many cases should) be more than one Executor running for
    a single queue.
    
    """
    
    class Meta:
        app_label = 'core'
        db_table = 'norc_executor'
    
    objects = QuerySetManager()
    
    class QuerySet(Daemon.QuerySet):
        
        def for_queue(self, q):
            """Executors pulling from the given queue."""
            return self.filter(queue_id=q.id,
                queue_type=ContentType.objects.get_for_model(q).id)
    
    @property
    def instances(self):
        """A custom implementation of the Django related manager pattern."""
        return MultiQuerySet(*[i.objects.filter(executor=self.pk)
            for i in INSTANCE_MODELS])
    
    # All the statuses executors can have.  See constants.py.
    VALID_STATUSES = [
        Status.CREATED,
        Status.RUNNING,
        Status.PAUSED,
        Status.STOPPING,
        Status.ENDED,
        Status.ERROR,
        Status.KILLED,
    ]
    
    VALID_REQUESTS = [
        Request.STOP,
        Request.KILL,
        Request.PAUSE,
        Request.RESUME,
    ]
    
    # The status of this executor.
    status = PositiveSmallIntegerField(default=Status.CREATED,
        choices=[(s, Status.NAME[s]) for s in VALID_STATUSES])
    
    # A state-change request.
    request = PositiveSmallIntegerField(null=True,
        choices=[(r, Request.NAME[r]) for r in VALID_REQUESTS])
    
    # The queue this executor draws task instances from.
    queue_type = ForeignKey(ContentType)
    queue_id = PositiveIntegerField()
    queue = GenericForeignKey('queue_type', 'queue_id')
    
    # The number of things that can be run concurrently.
    concurrent = IntegerField()
    
    @property
    def alive(self):
        return self.status == Status.RUNNING and self.heartbeat > \
            datetime.utcnow() - timedelta(seconds=HEARTBEAT_FAILED)
    
    def __init__(self, *args, **kwargs):
        super(type(self), self).__init__(self, *args, **kwargs)
        self.processes = {}
    
    def run(self):
        """Core executor function."""
        if settings.BACKUP_SYSTEM:
            self.pool = ThreadPool(5)
        self.log.info("%s is now running on host %s." % (self, self.host))
        
        # Main loop.
        while not Status.is_final(self.status):
            if self.request:
                self.handle_request()
            if self.status == Status.RUNNING:
                while len(self.processes) < self.concurrent:
                    self.log.debug("Popping instance...")
                    instance = self.queue.pop()
                    if instance:
                        self.log.debug("Popped %s" % instance)
                        self.start_instance(instance)
                    else:
                        self.log.debug("No instance in queue.")
                        break
            elif self.status == Status.STOPPING and len(self.processes) == 0:
                self.set_status(Status.ENDED)
                self.save(safe=True)
            # Clean up completed tasks before iterating.
            for pid, p in self.processes.items()[:]:
                p.poll()
                self.log.debug(
                    "Checking pid %s: return code %s." % (pid, p.returncode))
                if not p.returncode == None:
                    i = p.instance.__class__.objects.get(pk=p.instance.pk)
                    self.log.info("Instance '%s' ended with status %s." %
                        (i, Status.NAME[i.status]))
                    del self.processes[pid]
                    if settings.BACKUP_SYSTEM:
                        self.pool.queueTask(self.backup_instance_log, [i])
            self.wait(EXECUTOR_PERIOD)
            self.request = Executor.objects.get(pk=self.pk).request
    
    def clean_up(self):
        if settings.BACKUP_SYSTEM:
            self.pool.joinAll()
    
    def start_instance(self, instance):
        """Starts a given instance in a new process."""
        instance.executor = self
        instance.save()
        self.log.info("Starting instance '%s'..." % instance)
        # p = Process(target=self.execute, args=[instance.start])
        # p.start()
        ct = ContentType.objects.get_for_model(instance)
        p = Popen('norc_taskrunner --ct_pk %s --target_pk %s' %
            (ct.pk, instance.pk), shell=True)
        p.instance = instance
        self.processes[p.pid] = p
    
    # This should be used in 2.6, but with subprocess it's not possible.
    # def execute(self, func):
    #     """Calls a function, then sets the flag after its execution."""
    #     try:
    #         func()
    #     finally:
    #         self.flag.set()
    
    def handle_request(self):
        """Called when a request is found."""
        self.log.info("Request received: %s" %
            Executor.REQUESTS[self.request])
        
        if self.request == Executor.REQUEST_PAUSE:
            self.set_status(Status.PAUSED)
        
        elif self.request == Executor.REQUEST_RESUME:
            if self.status != Status.PAUSED:
                self.log.info("Must be paused to resume; clearing request.")
            else:
                self.set_status(Status.RUNNING)
        
        elif self.request == Executor.REQUEST_STOP:
            self.set_status(Status.STOPPING)
        
        elif self.request == Executor.REQUEST_KILL:
            # for p in self.processes.values():
            #     p.terminate()
            for pid, p in self.processes.iteritems():
                self.log.info("Killing process for %s." % p.instance)
                os.kill(pid, signal.SIGTERM)
            self.set_status(Status.KILLED)
        
        self.request = None
        self.save()
    
    def save(self, *args, **kwargs):
        """Overwrites Model.save().
        
        We have to be very careful to never overwrite a request, so
        often the request must be read from the database prior to saving.
        The safe parameter being set to True enables this behavior.
        
        """
        if kwargs.pop('safe', False):
            try:
                self.update_request()
            except Exception:
                pass
        Model.save(self, *args, **kwargs)
    
    def update_request(self):
        """Updates the request field from the database.
        
        There doesn't appear to be an easy way to have Django refresh an
        object from the database, so this method just updates the status.
        
        """
        if hasattr(self, 'id'):
            self.request = Executor.objects.get(id=self.id).request
            self.last_request_update = datetime.utcnow()
            return self.request
    
    def backup_instance_log(self, instance):
        self.log.info("Attempting upload of log for %s..." % instance)
        if backup_log(instance.log_path):
            self.log.info("Completed upload of log for %s." % instance)
        else:
            self.log.info("Failed to upload log for %s." % instance)
    
    @property
    def log_path(self):
        return 'executors/executor-%s' % self.id
    
    def __unicode__(self):
        return u"<Executor #%s on %s>" % (self.id, self.host)
    
    __repr__ = __unicode__
    
