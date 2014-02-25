#!/usr/bin/env python
# coding: utf-8
"""
Progress Tracker
"""

# Python 2.7 Standard Library
from __future__ import division
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
        The signature of the function that is created by `handler_ = handler()` 
        shall be (with positional arguments):

            def handler_(progress, elapsed, remaining, result)
    """
    if dt == 0.0:
        raise ValueError("dt=0.0 is invalid, it shall be positive (or None).")

    def broken(function):
        if handler is not None:
            handler_ = handler()
        else:
            handler_ = None

        def broken_(*args, **kwargs):
            generator = function(*args, **kwargs)
            t0 = t = None
            multiplier = None
            while True:
                try:
                    progress, result = generator.send(multiplier)
                    if t0 is None: # first yield
                        t0 = t = time.time()
                        progress = 0.0
                        rt = float("nan")
                    else:
                        t_ = time.time()
                        dt_ = t_ - t
                        t = t_
                        if dt is not None:
                            try:
                                multiplier = dt / dt_
                            except ZeroDivisionError:
                                multiplier = float("inf")
                        try:
                            rt = (1.0 - progress) / progress * (t - t0)
                        except ZeroDivisionError:
                            if progress < 1.0:
                                rt = float("inf")
                            else:
                                rt = float("nan")
                    if handler_ is not None:
            # TODO: change the "positional arguments" policy ? Actually it sucks.
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


# This is ugly.
def printer():
    def _printer(*args):
        print args
    return _printer

def counter0(n):
    result = 0
    while result < n:
        time.sleep(0.1); result = result + 1
    return result

@breakpoint(handler=printer)
def counter1(n):
    result = 0
    while result < n:
        # measure progress (as a float in [0,1])
        progress = result / n
        # export the progress and partial result
        yield progress, result
        # perform the actual computation
        time.sleep(0.1); result = result + 1
    # progress is 1.0 and the result is final
    yield 1.0, result

# The int/float counter threshold is actually nifty, because it is adaptative
# despite the discrete constraint on the loop atoms. It is asymptotically exact ?
# Is the mean elapsed time equal to the target elapsed time ?

@breakpoint(dt=1.0, handler=printer)
def counter2(n):
    result = 0
    counter, threshold = 1, 1.0
    while result < n:
        # time to yield ?
        if counter >= threshold:
            counter = 0
            progress = result / n
            multiplier = yield progress, result
            if multiplier is not None:
                 threshold = multiplier * threshold
        time.sleep(0.1); result = result + 1
        counter += 1
    yield 1.0, result

# Q: Its it worth partially "hiding" the pattern into a helper class and opaque
#    objects ? Would become something like below. I don't know really. It's
#    maybe slightly more explicit but probably slower and less hackable ...

@breakpoint(dt=1.0, handler=printer)
def counter2_with_helper(n):
    result = 0
    watchdog = Watchdog()
    while result < n:
        # time to yield ?
        if watchdog.ready:
            progress = result / n
            watchdog.update((yield progress, result))
            watchdog.reset()
        time.sleep(0.1); result = result + 1
        watchdog.next()
    yield 1.0, result

# Could also try an iterator pattern where __iter__ provides instantation
# and next, well, is next... Study that possibility, see if it leads to
# a simpler and more consistent API. For one, can we 'merge' the iteration
# of the computation and the iteration on the watchdog ? with izip ?
# What is the watchdog supposed to return as a value ? Something that we 
# can call `update` on ? Better name than watchdog ?

# Think of the clock / alarm metaphor. Drop the dt in the decorator, 
# instead instante an alarm, set its dt, then iterate on the alarm (clock)
# and test if it's triggered (atttribute), if this is the, case, you
# need to yield and somehow to send the result to the alarm (update method ?)
# That could be a nice and readable pattern actually ...
# Actually, if we drop the dt in the decorator, most of the timing logic
# would be transferred to alarm right ? Study that ...

# example where we stop after 10 sec ? Can we make the handler do something
# such as return a value ? Should we define a special exception for that that
# would encapsulate the early result ? PartialResult(result) ? Or play with the
# return value of handler ? (if any, this is an early result ? but then what
# if the result should be None ? We could already do that by raising 
# StopIteration, so that's only if we want to provide an early result THAT
# IS SOMETHING ELSE THEN THE PARTIAL RESULT ! Exception would be a good fit
# for that situation ...
# NB: we could be in the situation where we want to examine manually the
# partial result and then RESUME the computation. Can we support that ?

@breakpoint(handler=timeout(10.0, abort=False))
def wait(N=100):
    for i in range(N):
        print "i:", i
        yield float(i) / N, i
        time.sleep(1.0)
    yield 1.0, True


