import logging
import random
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
            delay = conf.get("delay", self.delay) + \
                    random.random() * conf.get("jitter", self.jitter)
            if self.out(line, delay, conf.get("interrupt", False)):
                return

    def cmd_wait(self, conf):
        delay = conf.get("delay", self.delay) + \
                random.random() * conf.get("jitter", self.jitter)
        data = raw_input(conf["prompt"])
        if conf.get("echo", False):
            self.out(data, delay)
        if conf["loop"]:
            while data != conf["for"]:
                data = raw_input(conf["prompt"])
                if conf.get("echo", False):
                    self.out(data, delay)
        else:
            raise NotImplementedError

    def run(self):
        LOG = logging.getLogger("DummySys.drivers.lava.uboot")

        y_conf = yaml.load(open(self.cmdfile))
        for cmd in y_conf:
           if cmd["cmd"] == "wait": 
                self.cmd_wait(cmd)
           elif cmd["cmd"] == "print":
                self.cmd_print(cmd)
           else:
                raise NotImplementedError
