import logging
import random
import re
import select
import sys
import time
import yaml

from lib.drivers import Driver


class UBoot(Driver):

    name = "lava-uboot"
    description = "A Dummy u-boot board that can interact with lava"

    def __init__(self, conf):
        self.cmdfile = conf["cmdfile"]
        self.delay = conf.get("delay", 0.001)
        self.jitter = conf.get("jitter", 0.005)
        self.ctx = conf.get("context", {})

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
            # Transform the lines if needed
            line = line.format(**self.ctx)
            # Print with some delay
            delay = conf.get("delay", self.delay) + \
                    random.random() * conf.get("jitter", self.jitter)
            if self.out(line, delay, conf.get("interrupt", False)):
                return

    def cmd_sleep(self, conf):
        time.sleep(conf["value"])

    def cmd_wait(self, conf):
        delay = conf.get("delay", self.delay) + \
                random.random() * conf.get("jitter", self.jitter)

        regexp = re.compile(conf["for"])
        while True:
            data = raw_input(conf["prompt"])
            m = regexp.match(data)
            if conf.get("echo", False):
                self.out(data, delay)

            if m is not None:
                self.ctx.update(m.groupdict())
                break

            if conf.get("fail", False):
                self.out(conf.get("fail"), delay)

    def run(self):
        LOG = logging.getLogger("DummySys.drivers.lava.uboot")

        y_conf = yaml.load(open(self.cmdfile))
        for cmd in y_conf:
           if cmd["cmd"] == "wait": 
                self.cmd_wait(cmd)
           elif cmd["cmd"] == "print":
                self.cmd_print(cmd)
           elif cmd["cmd"] == "sleep":
                self.cmd_sleep(cmd)
           else:
                raise NotImplementedError
