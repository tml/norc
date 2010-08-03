
"""General logging utilities."""

import os
import sys
import datetime
import traceback

from norc.settings import LOGGING_DEBUG, NORC_LOG_DIR

def make_log(norc_path, debug=None):
    """Make a log object with a subpath of the norc log directory."""
    return FileLog(os.path.join(NORC_LOG_DIR, norc_path), debug=debug)

def timestamp():
    """Returns a string timestamp of the current time."""
    return datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S.%f')

class Log(object):
    """Abstract class for creating a text log."""
    
    INFO = 'INFO'
    ERROR = 'ERROR'
    DEBUG = 'DEBUG'
    
    @staticmethod
    def format(msg, prefix):
        """The format of all log messages."""
        return '[%s] %s: %s\n' % (timestamp(), prefix, msg)
    
    def __init__(self, debug):
        """Initialize a Log object.
        
        If debug is not given, it defaults to the
        LOGGING_DEBUG setting of Norc.
        
        """
        self.debug = debug if debug != None else LOGGING_DEBUG
    
    def info(self, msg):
        """Log some informational message."""
        raise NotImplementedError
    
    def error(self, msg, trace):
        """Log about an error that occurred, with optional stack trace."""
        raise NotImplementedError
    
    def debug(self, msg):
        """Message for debugging purposes; only log if debug is true."""
        raise NotImplementedError
    

class FileLog(Log):
    """Implementation of Log that sends logs to a file."""
    
    def __init__(self, out=None, err=None, debug=None, echo=False):
        """ Parameters:
        
        out     Path to the file that output should go in.  Defaults
                to sys.stdout if no string is given.
        err     Path to the file that error output should go in.  Defaults
                to out if out is given and sys.stderr if it isn't.
        debug   Boolean; whether debug output should be logged.
        echo    Echoes all output to stdout if True.
        
        """
        Log.__init__(self, debug)
        self.out = open(out, 'a') if out else sys.stdout
        if not err and out:
            self.err = self.out
        else:
            self.err = open(err, 'a') if err else sys.stderr
        # Don't echo if already outputting to stdout.
        self.echo = echo and out
    
    def write(self, stream, msg):
        stream.write(msg)
        stream.flush()
        if self.echo:
            print >>sys.__stdout__, msg
    
    def info(self, msg):
        self.write(self.out, Log.format(msg, Log.INFO))
    
    def error(self, msg, trace=False):
        self.write(self.err, Log.format(msg, Log.ERROR))
        if trace:
            self.write(self.err, traceback.format_exc())
    
    def debug(self, msg):
        if self.debug:
            self.write(self.out, Log.format(msg, Log.DEBUG))
    
    def start_redirect(self):
        """Redirect all stdout and stderr to this log's files."""
        sys.stdout = self.out
        sys.stderr = self.err
    
    def stop_redirect(self):
        """Restore stdout and stderr to their original values."""
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
    
    def close(self):
        if self.out.name != '<stdout>':
            self.out.close()
        if self.err.name != '<stderr>' and self.err.name != '<stdout>':
            self.err.close()
    
    def __del__(self):
        """Destructor to make sure log files are closed."""
        self.close()
    

class S3Log(FileLog):
    """Outputs logs to S3 in addition to a local file."""
    
    # def __init__(self, *args, **kwargs):
        # FileLog.__init__(self, *args, **kwargs)
        
    def close(self):
        if not self.closed:
            FileLog.close(self)
            pass
            self.closed = True
