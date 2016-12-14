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

import random
import re
import select
import sys
import tarfile
import time


class FSM(object):
    def __init__(self, cmds, delay, jitter, ctx):
        self.cmds = cmds
        self.delay = delay
        self.jitter = jitter
        self.ctx = ctx
        self.handlers = {
            "execute": self.cmd_execute,
            "include": self.cmd_include,
            "print": self.cmd_print,
            "sleep": self.cmd_sleep,
            "wait": self.cmd_wait,
        }

    def run(self):
        for cmd in self.cmds:
            LOG.debug("New command: %s", cmd)
            try:
                self.handlers[cmd['cmd']](cmd)
            except KeyError:
                raise NotImplementedError

    def _delay(self, conf):
        delay = conf.get("delay", self.delay)
        jitter = conf.get("jitter", self.jitter)
        return delay + random.random() * jitter

    def _out(self, msg, delay, can_interrupt=False):
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

    def cmd_execute(self, conf):
        raise NotImplementedError

    def cmd_include(self, conf):
        filename = conf["file"].format(**self.ctx)
        if "archive" in conf:
            archive = conf["archive"].format(**self.ctx)
            tar = tarfile.open(archive)
            filehandler = tar.extractfile(filename)
        else:
            filehandler = open(filename)

        # Recurse with another state machine
        fsm = FSM(filehandler.read(), self.delay, self.jitter, self.ctx)
        fsm.run()

    def cmd_print(self, conf):
        for line in conf["lines"]:
            line = line.format(**self.ctx)
            delay = self._delay(conf)
            if self._out(line, delay, conf.get("interrupt", False)):
                  return

    def cmd_sleep(self, conf):
        time.sleep(conf["value"])

    def cmd_wait(self, conf):
        regexp = re.compile(conf["for"])
        echo = conf.get("echo", False)
        fail_string = conf.get("fail", False)

        while True:
            data = input(conf["prompt"])
            m = regexp.match(data)
            if echo:
                self._out(data, self._delay())

            if m is not None:
                self.ctx.update(m.groupdict())
                break

            if fail_string:
                self.out(fail_string, self.delay())
