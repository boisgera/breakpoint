#!/usr/bin/env python
# coding: utf-8

"""    
Preamble: the `/' operator denotes "true division" in the sequel, 
          never integer division.

    >>> import breakpoint

    >>> _t = 0.0
    >>> def mock_timer():
    ...     return _t
    >>> time = breakpoint._timer = mock_timer

    >>> def mock_sleep(time):
    ...    global _t
    ...    _t = _t + time
    >>> sleep = mock_sleep

Simple function with breakpoints
--------------------------------------------------------------------------------

    >>> def count_to_with_breakpoints(n):
    ...     i = 0
    ...     while i < n:
    ...         yield
    ...         sleep(1.0); i = i + 1
    ...     yield i

    >>> function = breakpoint.function()
    >>> count_to = function(count_to_with_breakpoints)
    >>> count_to(3)
    3

Display time elapsed since the first yield
--------------------------------------------------------------------------------

    >>> def show_elapsed():
    ...     def handler(**kwargs):
    ...         print kwargs["elapsed"],
    ...     return handler
    >>> function = breakpoint.function(on_yield=show_elapsed)
    >>> count_to = function(count_to_with_breakpoints)
    >>> count_to(3)
    0.0 1.0 2.0 3.0
    3

Yield and display partial results
--------------------------------------------------------------------------------

    >>> def count_to_with_breakpoints(n):
    ...     i = 0
    ...     while i < n:
    ...         yield i
    ...         sleep(1.0); i = i + 1
    ...     yield i

    >>> def show_result():
    ...     def handler(**kwargs):
    ...         print kwargs["result"],
    ...     return handler

    >>> function = breakpoint.function(on_yield=show_result)
    >>> count_to = function(count_to_with_breakpoints)
    >>> count_to(3)
    0 1 2 3
    3

Yield and display progress info
--------------------------------------------------------------------------------

    >>> def count_to_with_breakpoints(n):
    ...     i = 0
    ...     while i < n:
    ...         progress = i / n
    ...         yield progress, i
    ...         sleep(1.0); i = i + 1
    ...     progress = i / n 
    ...     yield progress, i

    >>> def show_progress():
    ...     def handler(**kwargs):
    ...         print "{0:.2f}".format(kwargs["progress"]),
    ...     return handler

    >>> function = breakpoint.function(progress=True, on_yield=show_progress)
    >>> count_to = function(count_to_with_breakpoints)
    >>> count_to(3)
    0.00 0.33 0.67 1.00
    3

The introduction of the progress info in the values does not impact the 
behavior of partial values:

    >>> function = breakpoint.function(progress=True, on_yield=show_result)
    >>> count_to = function(count_to_with_breakpoints)
    >>> count_to(3)
    0 1 2 3
    3

The availability of a progress provide an estimate for remaining time:

    >>> def show_time():
    ...     def handler(**kwargs):
    ...         elapsed, remaining = kwargs["elapsed"], kwargs["remaining"]
    ...         print "elapsed:", elapsed, "-- remaining:", remaining
    ...     return handler

    >>> function = breakpoint.function(progress=True, on_yield=show_time)
    >>> count_to = function(count_to_with_breakpoints)
    >>> count_to(3)
    elapsed: 0.0 -- remaining: nan
    elapsed: 1.0 -- remaining: 2.0
    elapsed: 2.0 -- remaining: 1.0
    elapsed: 3.0 -- remaining: 0.0
    3

Breakpoint period adaptation
--------------------------------------------------------------------------------

We can specify the time `dt` that we would like to have between two breakpoints.
This information is available as a breakpoint period multiplier send at each
breakpoint. Having multiplier equal to 2.0 for example means that the previous
period between two breakpoints was too short by a factor of 2.0.

In this example, the information is displayed, but the function does not adapt
its behavior to satisfy the requirement:

    >>> def count_to_with_breakpoints(n):
    ...     i = 0
    ...     while i < n:
    ...         progress = i / n
    ...         x = yield progress, i
    ...         print "x:", x
    ...         sleep(1.0); i = i + 1
    ...     progress = i / n 
    ...     yield progress, i

We can use a dedicated handler to see how the effective period between 
breakpoints stays the same despite the information sent to the function
at each breakpoint.

    >>> def show_dt():
    ...     t = [None]
    ...     def handler(**kwargs):
    ...         if t[0] is not None: # skip first call
    ...             print "dt: {0},".format(time() - t[0]),
    ...         t[0] = time()
    ...     return handler

    >>> function = breakpoint.function(progress=True, dt=2.0, on_yield=show_dt)
    >>> count_to = function(count_to_with_breakpoints)
    >>> count_to(10)
    x: None
    dt: 1.0, x: 2.0
    dt: 1.0, x: 2.0
    dt: 1.0, x: 2.0
    dt: 1.0, x: 2.0
    dt: 1.0, x: 2.0
    dt: 1.0, x: 2.0
    dt: 1.0, x: 2.0
    dt: 1.0, x: 2.0
    dt: 1.0, x: 2.0
    dt: 1.0,
    10

The code of the function shall be adapted to solve this issue:

    >>> def count_to_with_breakpoints(n):
    ...     i = 0
    ...     count, threshold = 0, 1
    ...     while i < n:
    ...         count += 1
    ...         if count >= threshold:
    ...             count = 0
    ...             progress = i / n
    ...             x = yield progress, i
    ...             print "x:", x
    ...             if x is not None:
    ...               threshold = int(round(x * threshold))
    ...               threshold = max(1, threshold)
    ...         sleep(1.0); i = i + 1
    ...     progress = i / n 
    ...     yield progress, i

    >>> function = breakpoint.function(progress=True, dt=2.0, on_yield=show_dt)
    >>> count_to = function(count_to_with_breakpoints)
    >>> count_to(10)
    x: None
    dt: 1.0, x: 2.0
    dt: 2.0, x: 1.0
    dt: 2.0, x: 1.0
    dt: 2.0, x: 1.0
    dt: 2.0, x: 1.0
    dt: 1.0,
    10

TODO: move the test below to the `alarm` branch, do not include in the master.
The API is not stable yet.

To avoid the duplication of this low-level code, the pattern has been factored 
out in the `Alarm` class:

    >>> def count_to_with_breakpoints(n):
    ...     i = 0
    ...     alarm = breakpoint.Alarm()
    ...     while i < n:
    ...         if alarm.next():
    ...             progress = i / n
    ...             x = yield progress, i
    ...             print "x:", x
    ...             alarm.update(x)
    ...         sleep(1.0); i = i + 1
    ...     progress = i / n 
    ...     yield progress, i

    >>> function = breakpoint.function(progress=True, dt=2.0, on_yield=show_dt)
    >>> count_to = function(count_to_with_breakpoints)
    >>> count_to(10)
    x: None
    dt: 1.0, x: 2.0
    dt: 2.0, x: 1.0
    dt: 2.0, x: 1.0
    dt: 2.0, x: 1.0
    dt: 2.0, x: 1.0
    dt: 1.0,
    10

"""

from __future__ import division # should be in the doctest, but it doesn't work.

#
# Test Runner
# ------------------------------------------------------------------------------
#

# Python 2.7 Standard Library
import doctest
import unittest
#import sys

__main__ = (__name__ == "__main__") 
#__name__ = "test"

#if __main__:
#    sys.modules[__name__] = sys.modules["__main__"]

test_suite = doctest.DocTestSuite() # for `python setup.py test`

if __main__:
    doctest.testmod()

