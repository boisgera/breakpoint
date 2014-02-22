#!/usr/bin/env python
# coding: utf-8
"""
Progress Tracker
"""

# Python 2.7 Standard Library
import time

#
# Metadata
# ------------------------------------------------------------------------------
#
__author__ = u"Sébastien Boisgérault <Sebastien.Boisgerault@mines-paristech.fr>"
__license__ = "MIT License"
__url__ = "https://github.com/boisgera/breakpoint" 
__version__ = "2.0.0"

#
# Misc. Notes
# ------------------------------------------------------------------------------
# keywords: breakpoint, timing, etc.
#
# Use partial result if any ? Demonstrate how a handler may decide to stop
# the iteration if it takes too long ?
#
# Demonstrate how to migrate an example to breakpoint, without breakpoint
# frequency control, then with it. Use a fibionnaci sequence example ?
#
# Show that the progress stuff is optional ? convention that None should be
# return when you have no idea what the outcome is.
#
# Use iterators/generators instead of threads ? The values obtained are
# progress < 1.0 until we obtain 1.0, then the last value is the result ?
# Nah, go for a StopIteration and get the previous value ? But before,
# we would try to use it as a progress ... end with yield 1.0, result ?
#
# Use the .send method to say if the frequency of the outputs should be
# increased / decreased (that may be ignored). What kind of message ?
# A frequency multiplier ? Yup. And the receiver is free to do something
# for example only if multiplier is > 2 or < 1/2.
#
# rt2 = (1.0 - new_progress) / (new_progress - progress) * dt_
# way to smooth the stuff ? With a weight that
# is more important for recent evaluations, but
# tempered by a (possibly large) collection of
# previous evals ?
# Recursive equations for the slope ? And deduce
# the remaining time ?
# - given DT/DP and dt/dp, how can we configure
#   to get dt/dp (easy !) and DT + dt / dp + Dp ?
# yes:
# DT + dt / dp + Dp = alpha dt/dp + (1-alpha) Dt/Dp
# with
# alpha = dp / (dp + Dp)
#
# -> introduce a 'beta' factor such as
# beta = 0 -> instant. slope and beta = 1 -> total
# slope ? Or fixed alpha ?
#
#
# Make dt optional ? Default to no time estimate or to 1.0 ?
# Make multiplier possibly return None ?
#
#
# Provide no progress estimate ?
#
# "Smoothing" options for remaining time estimate.
#
# replace handler with handlers ? Use *handlers ?
#
#
# Use the breakpoint decorated to extend the function signature ?
# That would allow dt and handlers to be given at runtime. We would
# stick to the convention that without extra parameters, the function
# is executed normally. Would that be more flexible ? That would allow
# use to get rid of the mandatory handler *factory* level, the user
# would instantiate the handlers as necessary.
#
# The extra arguments would be `_dt` and `_on_breakpoint` or `on_break`
# with a callable (or a list of callables). Underscores ? Really ?
# What if `dt` is already taken ... Distinguish static breakpoint 
# decorator and dynamic one ? Do we need to have two names ?
# or call with no arguments (or with arguments) dt, on_break and a
# last one, `dynamic` or `overridable`, etc., that if True, allows
# for the dt and handler arguments to be overriden at runtime
# (but then, on_break would be a handler, not a handler factory ?).
# Use `on_break_factory` in the static version ? urk ...
#
# OK, dynamic **is** necessary (for example, we may set dt from the 
# command-line, but the function call system suck. Maybe add a bunch
# of extra attributes to the function ? How can the function access
# those values ? OK, we return instead a callable instance, that one
# can access its attribute without any problem. See if that policy
# sticks ... Get rid of static / non-configurable decorator 
# arguments altogether ? Or keep them as a shortcut ?
#
# Can this policy be used on **methods** ?
#

def breakpoint(dt=None, handler=None):
    """
    Breakpoint decorator

    Arguments:

      - `dt` is the target time between two successive generator yields. 
        The generator that is decorated is sent at each new stage a number
        that is a prescribed yield period multiplier, or `None` if no
        estimate is available.

      - `handler` is an optional function factory that is called at each step.
        The signature of the function that is created by `on = handler()` shall 
        be (with positional arguments):

            def on(progress, elapsed, remaining, result)
    """
    def broken(function):
        if handler is not None:
            handler_ = handler()
        else:
            handler_ = None

        def broken_(*args, **kwargs):
            generator = function(*args, **kwargs)
            t0 = t = time.time()
            multiplier = None
            while True:
                try:
                    progress, result = generator.send(multiplier)
                    dt_ = time.time() - t
                    if dt is not None:
                        try:
                            multiplier = dt / dt_
                        except ZeroDivisionError:
                            multiplier = float("inf")
                    t = t + dt_
                    try:
                        rt = (1.0 - progress) / progress * (t - t0)
                    except ZeroDivisionError:
                        rt = float("inf")
                    if handler_ is not None:
                        handler_(progress, t-t0, rt, result)
                except StopIteration:
                    return result
        return broken_
    return broken


#
# Handlers
# ------------------------------------------------------------------------------
#

# Handler Use Cases:
#   - printers (elapsed time mostly),
#   - "gimme what you got" (with exception of with return of the early result),
#   - "don't bother" (remaining time too long after the first few samples).

# go to the end (real timeout) or abort asap (estimated timeout) ?

class AbortException(Exception):
    def __init__(self, progress, elapsed, remaining, result):
        self.progress  = progress
        self.elapsed   = elapsed
        self.remaining = remaining
        self.result    = result
        self.args = (progress, elapsed, remaining, result)

def timeout(time, abort=True, asap=False):
    def handler_factory():
        large_remaining = [0]
        if abort and asap:
            def handler(progress, elapsed, remaining, result):
                if elapsed + remaining > time:
                    large_remaining[0] += 1
                    # tweakability ? Use a mean on remaining instead ? 
                    # Mean at least for 1% of the progress to be sure ?
                    if large_remaining[0] >= 5 and progress >= 0.01:
                        raise AbortException(progress, elapsed, remaining, result)
        elif abort and not asap:
            def handler(progress, elapsed, remaining, result):
                if elapsed >= time:
                    raise AbortException(progress, elapsed, remaining, result)
        else:
            def handler(progress, elapsed, remaining, result):
                if elapsed >= time:
                    raise StopIteration()
        return handler
    return handler_factory

#
# Test
# ------------------------------------------------------------------------------
#

def printer():
    def _printer(*args):
        print args
    return _printer

@breakpoint(dt=5.0, handler=printer)
def test(N=100000):
   count, stop = 0, 1.0
   for i in xrange(N):
       if count >= stop: # time to compute a new progress estimate 
                         # and partial result.
           count = 0
           progress = float(i) / N
           multiplier = yield progress, None
           print "x:", multiplier
           stop = multiplier * stop
       count += 1

       # the actual "work"
       time.sleep(0.001)

   yield 1.0, "Done"

def fib0(n):
    result = []
    a, b = 0, 1
    while a < n:
        time.sleep(0.1)
        a, b = b, a + b
        result.append(a)
    return result

# not gonna use dt here (no multiplier use), dt=None should be the default
@breakpoint(dt=0.001, handler=printer)
def fib1(n):
    result = []
    a, b = 0, 1
    while a < n:
        progress = float(a) / n
        yield progress, result
        time.sleep(0.1)
        a, b = b, a + b
        result.append(a)
    yield 1.0, result

@breakpoint(dt=1.0, handler=printer)
def fib2(n):
    result = []
    a, b = 0, 1
    counter, limit = 0, 1.0
    while a < n:
        if counter >= limit:
            counter = 0
            progress = float(a) / n
            multiplier = yield progress, result
            limit = max(1.0, multiplier * limit)
            print "***: x, l ***:", multiplier, limit

        time.sleep(0.1)
        a, b = b, a + b
        result.append(a)

        counter += 1

    yield 1.0, result

#
# go for Sieve of Eratosthenes example ?
#
# example where we stop after 10 sec ? Can we make the handler do something
# such as return a value ? Should we define a special exception for that that
# would encapsulate the early result ? EarlyResult(result) ? Or play with the
# return value of handler ? (if any, this is an early result ? but then what
# if the result should be None ? We could already do that by raising 
# StopIteration, so that's only if we want to provide an early result THAT
# IS SOMETHING ELSE THEN THE PARTIAL RESULT ! Exception would be a good fit
# for that situation ...
#

@breakpoint(handler=timeout(10.0, abort=False))
def wait(N=100):
    for i in range(N):
        print "i:", i
        yield float(i) / N, i
        time.sleep(1.0)
    yield 1.0, True


