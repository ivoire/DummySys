#!/usr/bin/python

import logging
import random
import re
import time
import yaml
import zmq

from lib.drivers import Driver


class LavaDispatcher(Driver):

    name = "lava-dispatch"
    description = "Dummy LAVA dispatch that only send logs back"

    def __init__(self, conf):
        self.job_id = conf['job_id']
        self.log_uri = conf["log_uri"]
        self.logfile = conf["logfile"]

    def run(self):
        LOG = logging.getLogger("DummySys.drivers.lava.dispatch")

        # Create the socket
        context = zmq.Context()
        sock = context.socket(zmq.PUSH)
        LOG.info("Connecting to master at %s", self.log_uri)
        sock.connect(self.log_uri)

        # load the logfile
        try:
            with open(self.logfile, "r") as log_in:
                lines = yaml.load(log_in.read())
        except (IOError, yaml.YAMLError) as exc:
           LOG.error("Unable to open logfile %s", self.logfile)
           LOG.exception(exc)
           return 1

        actions = []
        start_pattern = re.compile("^start: ([\d.]+) ([\w_-]+) ")
        end_pattern = re.compile("^([\w_-]+) duration: \d+\.\d+$")

        LOG.info("Sending the logs")
        counter = 0
        len_lines = len(lines)
        next_step = len_lines / 20.0

        for line in lines:
            # Print a counter regularly
            counter += 1
            if counter >= next_step:
                next_step += len_lines / 20.0
                LOG.info("Progess: %02d%% (%d/%d)",
                         counter / (len_lines * 1.0) * 100,
                         counter, len_lines)

            if line.get('info', None) is not None:
                level = "info"
            elif line.get("debug", None) is not None:
                level = "debug"
            else:
                level = None

            if level is not None and type(line[level]) is str:
                msg = line[level]

                m_start = start_pattern.match(msg)
                m_end = end_pattern.match(msg)
                if m_start is not None:
                    action_level = m_start.group(1)
                    action_name = m_start.group(2)
                    actions.append((action_level, action_name))
                    LOG.debug("Start of action %s (%s)", action_name, action_level)
                elif m_end is not None:
                    (action_level, action_name) = actions.pop()
                    assert(m_end.group(1) == action_name)
                    LOG.debug("End of action %s (%s)", action_name, action_level)

            sock.send_multipart([str(self.job_id), action_level, action_name,
                              yaml.dump([line])[:-1]])
            time.sleep(random.random() / 10.0)

        LOG.info("Sending logs ended")
