#!/usr/bin/env python

import os
import itertools

def ranges(i):
    for a, b in itertools.groupby(enumerate(i), lambda t: t[1] - t[0]):
        b = list(b)
        yield b[0][1], b[-1][1]


def get_extension(path):
    return path.split(os.extsep)[-1].lower()

