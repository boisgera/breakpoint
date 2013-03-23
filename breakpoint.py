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
__version__ = "1.0.1"

#
# Mics. Notes
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

def breakpoint(dt=1.0, handler=None):
    """
    Breakpoint decorator

    Arguments:

      - `dt` is the target time between two successive generator yields. 
        The generator that is decorated is sent at each new stage a number
        that is a prescribed yield frequency multiplier, or `None` if no
        estimate is available.

      - `handler` is an optional function that is called at each step. 
        Its signature shall be:

            def handler(progress, elapsed_time, remaining_time)
    """
    def broken(function):
        def broken_(*args, **kwargs):
            generator = function(*args, **kwargs)
            stop, result = None, None
            t0 = t = time.time()
            multiplier = None
            progress = 0.0
            while True:
                try:
                    new_progress = generator.send(multiplier)
                    if isinstance(new_progress, tuple):
                        new_progress, result = new_progress
                        stop = True
                    dt_ = time.time() - t
                    multiplier = dt / dt_
                    t = t + dt_
                    try:
                        rt = (1.0 - new_progress) / new_progress * (t - t0)

                    except ZeroDivisionError:
                        rt = float("inf")
                        #rt2 = float("inf") 
                    if handler is not None:
                        handler(new_progress, t-t0, rt)
                    if stop:
                        return result
                    progress = new_progress
                except StopIteration:
                     raise
        return broken_
    return broken

#
# Test
# ------------------------------------------------------------------------------
#

def handler(p, e, r):
    print p, e, r

@breakpoint(dt=1.0, handler=handler)
def test():
   a = 1
   f = 1.0
   N = 100000000
   m = 0
   for i in xrange(N):
       m = m % int(f)
       if m == 0:
           xfreq = (yield (float(i) / N))
           f = f * xfreq # cap xfreq ? log scale ? Limit to x0.1-x10.0
       a += 1
       m += 1
   yield 1.0, "bazinga"

