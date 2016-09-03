#!/usr/bin/python

class Driver(object):

    name = "<undefined>"
    description = "<undefined>"

    @classmethod
    def select(cls, name):
        for subclass in cls.__subclasses__():
            if subclass.name == name:
                return subclass
        raise NotImplementedError("No driver called '%s' found" % name)

    def run(self):
        raise NotImplementedError

    @classmethod
    def drivers(cls):
        names = [c.name for c in cls.__subclasses__()]
        names.sort()
        return names
