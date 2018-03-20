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
import os
import pexpect
import pexpect.fdpexpect
import random
import re
import select
import subprocess
import sys
import tarfile
import time


class FSM(object):
    def __init__(self, cmds, delay, jitter, ctx):
        self.cmds = cmds
        self.expect = pexpect.fdpexpect.fdspawn(sys.stdin.fileno(), encoding="utf-8")
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
        self.LOG = logging.getLogger("DummySys.fsm")
        for cmd in self.cmds:
            self.LOG.debug("Command: %s", cmd["cmd"])
            try:
                self.handlers[cmd["cmd"]](cmd)
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
                (r, _, _) = select.select([sys.stdin], [], [], delay)
                if sys.stdin in r:
                    # Remove the current line
                    sys.stdin.readline()
                    return True
            else:
                time.sleep(delay)
        sys.stdout.write("\n")
        return False

    def cmd_execute(self, conf):
        args = []
        # Check the program path
        prog = conf["args"][0]
        if prog.startswith("./"):
            # The program path is absolute, change it to be relative to the
            # DummySys base directory.
            path = os.path.join(os.path.dirname(__file__), "..",
                                os.path.dirname(prog),
                                os.path.basename(prog))
            conf["args"][0] = os.path.abspath(path)

        for arg in conf["args"]:
            args.append(arg.format(**self.ctx))
        ret = subprocess.call(args)
        # TODO: allow for a continue_on
        if ret in conf["quit_on"]:
            msg = conf["quit_on"][ret]
            raise Exception(msg)

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
        self.LOG.debug(" for: %s", conf["for"])
        for_data = ["\n", conf["for"] + "\n"]
        fail_string = conf.get("fail", False)

        while True:
            sys.stdout.write(conf["prompt"])
            sys.stdout.flush()
            index = self.expect.expect(for_data)
            if index == 0:
                if fail_string:
                    self._out(fail_string, self._delay(conf))
                continue

            self.ctx.update(self.expect.match.groupdict())
            return
