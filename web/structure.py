
"""Data structures and how to retrieve that data.

The dicts in this file describe what data should be returned for each
content type, and how to retrieve that data from the appropriate object.

"""

from django.conf import settings

from norc.core import report
from norc.norc_utils.parsing import parse_date_relative

def parse_since(since_str):
    """A utility function to help parse a since string."""
    if since_str == 'all':
        since_date = None
    else:
        try:
            since_date = parse_date_relative(since_str)
        except TypeError:
            since_date = None
    return since_date

def get_trss(nds, status_filter='all', since_date=None):
    """
    A hack fix so we can get the statuses for the proper daemon type.
    """
    if nds.get_daemon_type() == 'NORC':
        task_statuses = nds.taskrunstatus_set.all()
    else:
        task_statuses = nds.sqstaskrunstatus_set.all()
    status_filter = status_filter.lower()
    from norc.core.models import TaskRunStatus
    TRS_CATS = TaskRunStatus.STATUS_CATEGORIES
    if not since_date == None:
        task_statuses = task_statuses.filter(date_started__gte=since_date)
    if status_filter != 'all' and status_filter in TRS_CATS:
        only_statuses = TRS_CATS[status_filter.lower()]
        task_statuses = task_statuses.filter(status__in=only_statuses)
    return task_statuses

def get_sqsqueues():
    if 'norc.sqs' in settings.INSTALLED_APPS:
        from boto.sqs.connection import SQSConnection
        c = SQSConnection(settings.AWS_ACCESS_KEY_ID,
                          settings.AWS_SECRET_ACCESS_KEY)
        return c.get_all_queues()
    else:
        return []

# Provides a function to obtain the queryset
# of data objects for each content type.
RETRIEVE = {
    'daemons': lambda GET: report.ndss(parse_since(
        GET.get('since', '10m'))).order_by('-date_started'),
    'jobs': lambda _: report.jobs(),
    'sqsqueues': lambda _: get_sqsqueues(),
}

RETRIEVE_DETAILS = {
    'daemons': ('tasks', lambda cid: get_trss(report.nds(cid))),
    'jobs': ('iterations', lambda cid: report.iterations(cid)),
    'iterations': ('tasks', lambda cid: report.tasks_from_iter(cid)),
}

# Dictionary the simultaneously defines the data structure to be returned
# for each content type and how to retrieve that data from an object.
DATA = {
    'daemons': {
        'id': lambda nds, _: nds.id,
        'type': lambda nds, _: nds.get_daemon_type(),
        'region': lambda nds, _: nds.region.name,
        'host': lambda nds, _: nds.host,
        'pid': lambda nds, _: nds.pid,
        'running': lambda nds, _: len(get_trss(nds, 'running')),
        'success': lambda nds, GET: len(get_trss(nds, 'success',
                                        parse_since(GET.get('since')))),
        'errored': lambda nds, GET: len(get_trss(nds, 'errored',
                                        parse_since(GET.get('since')))),
        'status': lambda nds, _: nds.status,
        'started': lambda nds, _: nds.date_started,
        'ended': lambda nds, _: nds.date_ended if nds.date_ended else '-',
    },
    'jobs': {
        'id': lambda job, _: job.id,
        'name': lambda job, _: job.name,
        'description': lambda job, _: job.description,
        'added': lambda job, _: job.date_added,
    },
    'tasks': {
        'id': lambda trs, _: trs.id,
        'job': lambda trs, _: trs.task.job.name,
        'task': lambda trs, _: trs.task.get_name(),
        'status': lambda trs, _: trs.status,
        'started': lambda trs, _: trs.date_started,
        'ended': lambda trs, _: trs.date_ended,
    },
    'sqstasks': {
        'id': lambda trs, _: trs.id,
        'task_id': lambda trs, _: str(trs.get_task_id()),
        'status': lambda trs, _: trs.get_status(),
        'started': lambda trs, _: trs.date_started,
        'ended': lambda trs, _: trs.date_ended,
    },
    'iterations': {
        'id': lambda i, _: i.id,
        'status': lambda i, _: i.status,
        'type': lambda i, _: i.iteration_type,
        'started': lambda i, _: i.date_started,
        'ended': lambda i, _: i.date_ended if i.date_ended else '-',
    },
    'sqsqueues': {
        'id': lambda q, _: q.url.split('/')[-1],
        'num_items': lambda q, _: q.count(),
        'timeout': lambda q, _: q.get_timeout(),
    },
}
