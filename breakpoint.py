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
__version__ = "2.1.1"
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

