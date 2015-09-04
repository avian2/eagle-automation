#!/usr/bin/env python


class FileNotFoundError(IOError):
    pass


class BadExtension(Exception):
    pass


class DatabaseInvalid(Exception):
    pass

