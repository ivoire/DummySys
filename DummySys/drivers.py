# -*- coding: utf-8 -*-
# vim: set ts=4

# Copyright 2016 Rémi Duraffort
# This file is part of DummySys.
#
# DummySys is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# DummySys is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with DummySys.  If not, see <http://www.gnu.org/licenses/>


class Driver(object):
    name = "<undefined>"
    description = "<undefined>"

    @classmethod
    def select(cls, classname):
        for sub in cls.subclasses():
            if sub.classname == classname:
                return sub
        raise NotImplementedError("No driver called '%s' found" % name)

    def run(self):
        raise NotImplementedError

    @classmethod
    def subclasses(cls):
        subcls = []
        for sub in cls.__subclasses__():
            subcls.append(sub)
            child = sub.subclasses()
            if child is not []:
                subcls.extend(child)
        return subcls
