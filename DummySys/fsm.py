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

import logging
import pexpect.fdpexpect
import random
import select
import sys
import time


class FSM(object):
    def __init__(self, cmds, delay, jitter, ctx):
        self.cmds = cmds
        self.delay = delay
        self.jitter = jitter
        self.ctx = ctx
        self.handlers = {
            "wait": self.cmd_wait,
            "print": self.cmd_print,
        }
        self.connection = pexpect.fdpexpect.fdspawn(sys.stdin, encoding="utf-8", logfile=sys.stdout)

    def run(self):
        LOG = logging.getLogger("DummySys.FSM")
        for cmd in self.cmds:
            LOG.debug("New command: %s", cmd)
            try:
                self.handlers[cmd['cmd']](cmd)
            except KeyError:
                raise NotImplementedError

    def out(self, msg, delay, can_interrupt=False):
        for c in msg:
            sys.stdout.write(c)
            sys.stdout.flush()
            if can_interrupt:
                (r, w, x) = select.select([sys.stdin], [], [], delay)
                if sys.stdin in r:
                    # Remove the current line
                    sys.stdin.readline()
                    return True
            else:
                time.sleep(delay)
        sys.stdout.write("\n")
        return False


    def cmd_print(self, conf):
        for line in conf["lines"]:
            line = line.format(**self.ctx)
            delay = conf.get("delay", self.delay) + \
                    random.random() * conf.get("jitter", self.jitter)
            if self.out(line, delay, conf.get("interrupt", False)):
                  return

    def cmd_wait(self, conf):
        pass
