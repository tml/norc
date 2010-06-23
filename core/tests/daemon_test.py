
"""Module for testing anything related to daemons."""

import os
import threading

from django.test import TestCase

from norc import settings
from norc.core import reporter
from norc.core.daemons import ForkingNorcDaemon
from norc.core.models import NorcDaemonStatus
from norc.utils import init_db, wait_until

class DaemonThread(threading.Thread):
    """"""
    
    def __init__(self, daemon):
        # self.threading = threading
        threading.Thread.__init__(self)
        self.daemon = daemon
    
    def run(self):
        self.daemon.run()

class TestDaemons(TestCase):
    """Tests for Norc daemons.
    
    Creates a ForkingNorcDaemon in a new thread because if you use the
    command line utility (norcd) it does not use the Django test database.
    
    """
    
    def setUp(self):
        """Initialize the DB and start the daemon in a thread."""
        init_db.init_static()
        self.daemon = ForkingNorcDaemon(reporter.get_region('DEMO_REGION'),
            3, settings.NORC_LOG_DIR, False)
        DaemonThread(self.daemon).start()
        self.pid = os.getpid()
        # Use a lambda so that the status gets retreived each time
        # it's needed, instead of pulled from a cache.
        self.get_nds = lambda: \
            reporter.get_object(NorcDaemonStatus, pid=self.pid)
    
    def test_daemon_started(self):
        """Nice and simple test that the daemon is starting and then running.
        
        Daemon must be in the starting state and then transition to the
        running state within 3 seconds to pass this test.
        
        """
        # Is it safe to assume this will always pass, or will it
        # sometimes transition too quickly?
        self.assert_(self.get_nds().is_starting())
        wait_until(lambda: self.get_nds().is_running(), 3)\
    
    def tearDown(self):
        """Request the daemon stops and confirm that it does."""
        self.daemon.request_stop()
        wait_until(lambda: self.get_nds().is_done(), 3)
