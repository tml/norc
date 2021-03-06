



Norc Release v2.1.1
===================

## Features
  - Added host-wide functionality to norc_control, as well as a wait option.

## Tweaks:
  - The queue failure rate column has been removed due to slowness.
  - The Alive column has been removed and merged into the Status column
    as a color-coding.

## Bug Fixes:
  - Updated norc_control to work with new request design.
  - Fixed timeframe selection in the web interface.
  - Fixed a bug with saving in AbstractDaemon was allowing requests
    to be overwritten.
  - Added missing SQL commands to the migration doc.


Norc Release v2.1
=================

__SCHEMA CHANGES__, please see migration.md.

## Features
  - Scheduler now has a status and supports requests.
  - Support for changing a schedule after it's been made.
  - Schedules now have a deleted flag, making data deletion unnecessary.
  - New setting: STATUS_TABLES.  Custom-define what tables show up in
    the front end!
  - New command line utility "norc_control" for sending request to
    Executors and Schedulers.
  - S3 log backups are now compressed prior to uploading.

## Tweaks:
  - BaseInstance and BaseSchedule are now AbstractInstance and
    AbstractSchedule, respectively.
  - New base class AbstractDaemon for commonalities between Executor
    and Scheduler.
  - Log backing of instance logs is now done by a thread pool inside
    the Executor for that instance.

## Bug Fixes:
  - Front end controls for Executors and Schedulers now work again.
  - Fixed broken query for orphaned schedules.
  - Fixed signal registering in both Executor and Scheduler.


Norc Release v2.0
=================

## Features:
  - Full rewrite of Norc.  See design documentation, if it ever gets written.


Norc Release v1.1.2
===================

## Tweaks:
  - Fixed (or at least greatly improved) the horrible slowness of the
    daemons table in the front end by switching from len(queryset) to
    queryset.count().

## Bug Fixes:
  - Fixed the norc utility's displaying of SQS task counts.


Norc Release v1.1.1
===================

## Tweaks:
  - Improved FileLog in log_new.py to handle echoing to stdout and
    redirecting of both stdout and stderr.

## Bug Fixes:
  - Another attempted fix at the weird Perpetually bug involving
    recognizing daemons as SQS or NORC.
  - Half fixed the weird expanding cell bug when using the daemon control
    slideout.  Now there may be a 1px shift.


Norc Release v1.1
=================

## Features:
  - (DEV) New function init_test_db creates a suitable test database.
  - Several useful unit test for the web module now exist!
  - Better version of daemon control!  Vertical orientation, some lovely
    padding, and the security elements listed below.

## Security:
  - The daemon control interface only appears if the user is a superuser.
  - Even for superusers it now requires confirmation before trying the
    POST request.

## Tweaks:
  - Renamed init_db.py to just db.py.


Norc Release v1.0.2
===================

## Features:
  - Rudimentary version of daemon control through the status page.  Hover
    over a daemon status to get a menu.  Use with caution.

## Tweaks:
  - Added tmp/ and log/ directories to Norc by default.
  - An sqs_populate_db.py script now exists to add random SQS data.  It
    takes a long time to run because adds hundreds of thousands of items
    to the database.
  - Renamed structure.py to data_defs.py and rewrote it to use objects.
  - SQS data definitions now live inside the sqs/__init__.py file.
  - Added Iteration column to the task tables.

## Bug Fixes:
  - Loading indicators will now disappear if an AJAX request fails.
  - The get_daemon_type() function now checks for existence of sqstaskrunstatus_set before querying it.
  - Added timeframe filtering and ordering to SQS tasks.
  - Added ordering to failed tasks.


Norc Release v1.0.1
===================

## Features:
  - Added 'Failed Tasks' table, which shows all tasks with an error status.

## Tweaks:
  - Content is no longer centered.
  - display:table allows for intelligently sized content sections.
  - Clicking on a different task count cell now switches to showing those
    tasks, instead of just collapsing the details.
  - Fixed highlighting color of task count by status cells when the row
    is expanded.
  - The get_daemon_type hack in models.py no longer uses .count() for
    efficiency purposes.

## Bug Fixes:
  - Switched back a CSS class change that broke proper coloring of pagination.
  - Added the loading indicator to source control.
  - Improved how the indicator is displayed so that table cells
    don't get shifted.
  - An exception will be thrown if the NORC_ENVIRONMENT shell variable is
    not set.  Before it would default to 'BaseEnv', but since Django needs
    more settings than that to run, a custom environment is now enforced.


Norc Release v1.0
=================

## Features:
  - populate_db.py script in utils can fill your DB with large amounts of
    random data for testing.  Requires init_db to be run first from an
    empty database.
  - SINCE_FILTER dictionary in structures.py now allows a per data key
    definition of how to filter a data set using a since date.
  - ORDER dictionary in structures.py allows an optional per data key
    definition of how to order the results.
  - Added a map in status.js that allows customization of data tables.
  - Task selection by status: Click on the number of running/success/errored
    tasks for any daemon to reveal only those tasks.
  - Timestamp of the last full page refresh.
  - Loading indicator for any data retrieval.

## Tweaks:
  - Auto-reload is now disabled by default.
  - Hard-coded width of sqsqueues table to 50% (in status.css) to
    appease Darrell.

## Bug Fixes:
  - Subtables now reflect the correct timeframe (for real this time).
  - Removed erroneous reference in sqs/__init__.py to a test setting,
    SQSTASK_IMPLEMENTATIONS, that was not supposed to be committed.


Norc Release v0.9
=================

## Features:
  - Proper pagination of all subtables!
  - Highlighting of selected timeframe.
  - SQS Queue table now exists, with proper handling if SQS isn't enabled.
  - JSON response now uses a list, allowing for ordering of items.
  - Daemons are now ordered by descending time started.
  - There is now an auto-reload checkbox to disable it.
  - Middleware that lets you view the traceback of an exception caused
    by an AJAX request as plain text.

## Tweaks:
  - Default page size is now 20 for all table levels.
  - Detail tables with only one page no longer show the paging row.
  - Rows will no longer line-wrap; the table just grows horizontally.
  - More columns have been aligned properly.
  - Added ErrorHandlingMiddleware to the default middleware list.

## Bug Fixes:
  - Going from the nth page back to a timeframe with < n pages now works
    (goes back to the first page).
  - Options are now properly inherited from parent chains.  This means
    that subtables now reflect the selected timeframe.
  - Several other minor issues.
