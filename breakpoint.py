#!/usr/bin/env python
# coding: utf-8
"""
Breakpoint - Function Execution Tracker
"""

# Python 2.7 Standard Library
from __future__ import division
import time


# Third-Party Libraries
pass

#
# Metadata
# ------------------------------------------------------------------------------
#

__main__ = (__name__ == "__main__")

__name__    = "breakpoint"
__version__ = "2.1.0-alpha"
__license__ = "MIT License" 
__author__  = u"Sébastien Boisgérault <Sebastien.Boisgerault@mines-paristech.fr>"
__license__ = "MIT License"
__url__     = "http://boisgera.github.io/breakpoint" 
__summary__ = "Function Execution Tracker"
__readme__  = None
__classifiers__ = None

_timer = time.time # not part of the public API, used for mocks in tests.

def function(on_yield=None, progress=False, dt=None):
    """
    Transform a function with breakpoints (aka generator) into a function.

    The result of `function` can (and often will) be used as a decorator.

    Arguments
    ---------

      - `on_yield`: function handler factory.

        A call `handler = on_yield()` is performed every time the
        decorated generator is called. The object `handler` shall be 
        function-like ; it is called for every yield of the generator
        function, with the following keyword arguments:

          - `progress`: a floating-point number between `0.0` (when the
            function execution starts) and `1.0` (when it ends), or `None`
            when this information is not available.

          - `elapsed`: the time elapsed since the function call in seconds.

          - `remaining`: the estimated time to the end of the function, 
             in seconds, or `None` when no estimate is available.

          - `args`: positional arguments of the decorated generator.

          - `kwargs`: keyword arguments of the decorated generator.  

          - `result`: partial result of the decorated generator.

        If the handler returns a value that is not `None`, the decorated
        generator execution stops and this value is returned.

      - `progress`: `True` when the generator yields `(progress, result)`
        instead of `result`.

      - `dt` is the target time between two successive breakpoints, 
        or `None` if there is no such target.
 
        At every breakpoint, the generator receives a floating-point number;
        it is a multiplier that should be applied to the current period between
        breakpoints to reach the `dt` target.
        The multiplier may be `None` if no estimate is available.

    Returns
    -------

      - `decorator`: a decorator for generator functions.

    """
    if dt is not None:
        dt = float(dt)
        if dt < 0.0:
          error = "dt={0} is invalid, use a positive number (or None)."
          raise ValueError(error.format(dt))

    def decorator(generator_function):
        def function_(*args, **kwargs):
            if on_yield is not None:
                yield_handler = on_yield()
            else:
                yield_handler = None

            generator = generator_function(*args, **kwargs)
            t0 = t = None
            multiplier = None
            while True:
                try:
                    info = generator.send(multiplier)
                    if progress:
                        progress_, result = info
                    else:
                        progress_, result = None, info

                    if t0 is None: # first yield
                        t0 = t = _timer()
                        rt = float("nan")
                    else:
                        t_ = _timer()
                        dt_ = t_ - t
                        t = t_
                        if dt:
                            try:
                                multiplier = dt / dt_
                            except ZeroDivisionError:
                                multiplier = float("inf")
                        if progress_ is None:
                            rt = float("nan")
                        else:
                            try:
                                rt = (1.0 - progress_) / progress_ * (t - t0)
                            except ZeroDivisionError:
                                if progress < 1.0:
                                    rt = float("inf")
                                else:
                                    rt = float("nan")
                    if yield_handler:
                        handler_result = yield_handler(progress=progress_, 
                                                       elapsed=t-t0, 
                                                       remaining=rt, 
                                                       result=result, 
                                                       # not documented:
                                                       args=args,
                                                       kwargs=kwargs)

                        if handler_result is not None:
                            return handler_result # not documented feature.
                            # The case where we want to stop the execution
                            # *and* return None is not supported.
                except StopIteration:
                    return result
        function_.decorator = decorator
        function_.generator = generator_function
        return function_
    return decorator


#
# Misc. Notes and experiments
# ------------------------------------------------------------------------------

# Rk: today the real issue is the lack of support for adaptation of breakpoint
#     frequency adaptation, hence the efforts on alarm. Focus on that.

# TODO: add argspec to the arguments given to the handler ? 
#       To simplify the processing of the arguments ? Then we could also need
#       something like inspect "getcallargs", but with the argspec instead of 
#       the function.

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
# Can we change the handler / dt, afterwards ? Uhu that's tricky,
# we're talking handler factorries remember ?

#
# Can this policy be used on **methods** ?
#
# TODO: custom timer (for tests for example ?)
#
# Q: should we call the handler a last time when it's over with
#    a special flag ?
#
# Ability to "tune" the breakpoint parameters after the wrapping ?
#
# Should we memorize all yield times and the starting point ?
# And communicate all this to the handler so that it can perform
# more complex computations that we do ? That may be overkill for
# now ...

# rename `handler` as `on_yield` ? `on_breakpoint` ? Is it readable when
# we DON'T use the argument name at all ?

# Q: make handler mandatory ?

# TODO: add a "no_progress" parameter to break point ? That would be handy.
#       or explicit progress=True ? Which one is the best ? Probably the
#       latter. Err ... when dt is set, we do need progress actually, 
#       otherwise it makes little sense. Can we omit the progress attribute
#       then ? Can we forget about progress and accept `dt=True` instead ?
#       That's not very explicit, but that may be good enough ... Try it !

# TODO: investigate the use of wrapt


# TODO: sort the mess and move the interesting bits (alarm ?) to another branch.

#
# Handlers
# ------------------------------------------------------------------------------
#

def debug():
    def debug_(**kwargs):
        for name in "progress elapsed remaining result args kwargs".split(): 
            print name + ":", kwargs[name]
    return debug_

class AbortException(Exception):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def timeout(time, abort=True, asap=False):
    def handler_factory():
        large_remaining = [0]
        if abort and asap:
            def on_yield(**kwargs):
                elapsed = kwargs["elapsed"]
                remaining = kwargs["remaining"]
                progress = kwargs["progress"]
                if elapsed + remaining > time:
                    large_remaining[0] += 1
                    if large_remaining[0] >= 5 and progress >= 0.01:
                        raise AbortException(**kwargs)
        elif abort and not asap:
            def on_yield(**kwargs):
                elapsed = kwargs["elapsed"]
                if elapsed >= time:
                    raise AbortException(**kwargs)
        else:
            def on_yield(**kwargs):
                elapsed = kwargs["elapsed"]
                if elapsed >= time:
                    raise StopIteration()
        return on_yield
    return handler_factory

#
# Generators
# ------------------------------------------------------------------------------
#

def count_to(n, wait=0.1):
    i = 0
    while i < n:
        yield i
        time.sleep(wait)
        i = i + 1
    yield i













def printer():
    def _printer(**kwargs):
        for name in kwargs:
            print name + ":", kwargs["name"]  
    return _printer

def counter0(n):
    result = 0
    while result < n:
        time.sleep(0.1); result = result + 1
    return result

@function(on_yield=printer)
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

@function(dt=1.0, on_yield=printer)
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

@function(dt=1.0, on_yield=printer)
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

# ------------------------------------------------------------------------------
# TODO: move the "Alarm" experiment to another branch.

# Think of the clock / alarm metaphor. Drop the dt in the decorator, 
# instead instante an alarm, set its dt, then iterate on the alarm (clock)
# and test if it's triggered (atttribute), if this is the, case, you
# need to yield and somehow to send the result to the alarm (update method ?)
# That could be a nice and readable pattern actually ...
# Actually, if we drop the dt in the decorator, most of the timing logic
# would be transferred to alarm right ? Study that ...
# UPDATE: return the triggered status by next(), that's so much simpler.

# AAAAH. The pb with the alarm is that we would set the interrupt from
# within the function while it should be done outside. Keep dt in the
# decorator. Hmmm ... think of it more.

# TODO: forget the float threshold, that's too smart, go with integers.
#       this way, we can make sure that the threshold is never zero.

class Alarm(object):
    def __init__(self):
        self.count = 0
        self.threshold = 1
    def __iter__(self):
        return self
    def next(self):
        self.count += 1
        return (self.count >= self.threshold)
    def update(self, multiplier):
        self.count = 0
        if multiplier is not None:
            self.threshold = int(round(multiplier * self.threshold))
            self.threshold = max(1, self.threshold)

@function(on_yield=printer, dt=1.0)
def counter2_alarm(n):
    result = 0
    alarm = Alarm()
    for result in range(n):
        if alarm.next():
            progress = result / n
            alarm.update((yield progress, result))
        time.sleep(0.1); result = result + 1
    yield 1.0, result

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

@function(on_yield=timeout(10.0, abort=False))
def wait(N=100):
    for i in range(N):
        print "i:", i
        yield float(i) / N, i
        time.sleep(1.0)
    yield 1.0, True

#
# Documentation Examples
# ------------------------------------------------------------------------------
#

# TODO: get the documentation, transform code blocks into interpreter statements
#       when they are not in this form and doctest the result. Also define a 
#       module with all the code defined in the documentation ? (not the interpreter
#       chunks).

import time

def inc(n):
    time.sleep(0.1)
    return n + 1

def count_to_three():
    result = 0
    result = inc(result)
    result = inc(result)
    result = inc(result)
    return result

assert count_to_three() == 3

def count_to_three():
    result = 0
    yield
    result = inc(result)
    yield
    result = inc(result)
    yield
    result = inc(result)
    yield result

counter = count_to_three()
counter.next()
counter.next()
counter.next()
assert counter.next() == 3

def count_to(n):
    result = 0
    for i in range(n):
        yield result
        result = inc(result)
    yield result

def print_partial():
   def print_partial_(**kwargs):
       print kwargs.get("result"),
   return print_partial_

def fibionacci_generator():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def stack(stop):
    def handler_factory():
        results = []
        def handler(result, **extra):
            if stop(result):
                return results
            results.append(result)
        return handler
    return handler_factory

# TODO: can we simplify the passing of arguments to the handler ? Maybe if the
#       function arguments where automatically transferred to the handler as
#       args and kwargs ? Grmph, that is not very pretty because to be useful,
#       the handler would have to implement code for the normalization of
#       positional vs keyword arguments ...

def fibionacci(n):
    def stop(result):
        return result > n
    wrapper = function(stack(stop))
    return wrapper(fibionacci_generator)()

# ------------------------------------------------------------------------------

def generator(x0):
    while True:
        yield x0
        x0 = x0 - 0.5 * (x0 - 2.0 / x0)

def min_step(eps):
    def handler_factory():
        x = [None]
        def handler(result, **extra):
            x0, x1 = x[0], result
            if x0 is not None:
                step = abs(x1 - x0)
                if step < eps:
                    return x1
            x[0] = x1
        return handler
    return handler_factory

def fixed_point(generator, x0, eps=1e-17):
    wrapper = function(handler=min_step(eps))
    return wrapper(generator)(x0)

