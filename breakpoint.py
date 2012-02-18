#!/usr/bin/env python

import time

# is dt of any use ? Two issues: filter the callback calls (but that can
# be done as a post-processing step) and adapt (reduce / increase) the 
# number of yields. But that step INCREASES the complexity of client code
# ... instead the client should roughly know how to subdivide the stuff
# right ? Anyway, the fine tweaking with the number of steps should be
# optional (or not implemented), but not in the way.

# TODO: manage dt = None (aka callback at every yield).

# TODO: can we use python generator to STOP the function (if the partial
#       computations we have are good enough ?). With a StopIteration
#       in the callback ?

# TODO: possible that progress is Unknown (None) if we STREAM something
#       for example ... Handle this case => Invert the pattern, and
#       put progress second ? That would allow some yield value at the end ?
#       Arf that would be ambigous if the return value is a tuple already ...
#       Too bad ! Or pack everything that is not a value in a custom class ?
#       And introspect the stuff ? Progress class ?


def split(dt=0.0, callback=None):
    def splitter(function):
        return Splitted(function, dt, callback)
    return splitter

class Splitted(object):
    def __init__(self, function, dt, callback):
        self.function = function
        self.dt = dt
        self.callback = callback
    def __call__(self, *args, **kwargs):
        iterator = self.function(*args, **kwargs)
        callback = self.callback or (lambda: None)
        self.t = self.t0 = time.time()
        for progress, value in iterator:
            dt = time.time() - self.t
            if dt >= self.dt:
                self.t = self.t + dt
                callback(progress, value, self.t - self.t0)                
        return value

def display(progress, value, elapsed):
    print "{0} %, {1} s.".format(progress*100, elapsed)

@split(dt=5.0, callback=display)
def try_me(count=100000000):
    for i in range(count):
        pass
        yield (float(i+1) / count, None)
    yield (1.0, count)

if __name__ == "__main__":
    print try_me()





