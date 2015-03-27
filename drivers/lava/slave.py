#!/usr/bin/python

import logging
import time
import zmq


class Job(object):
  def __init__(self):
    self.running = False

  def run(self, zmq_ctx):
    # TODO: send data to the master
    pass


class Driver(object):
  def __init__(self, conf):
    self.name = "lava-slave"
    self.description = "Lava ZMQ slave"
    self.hostname = conf['hostname']
    self.send_queue = conf['send_queue']
    self.master_uri = conf['master_uri']
    self.log_uri = conf['log_uri']
    self.timeout = conf['timeout']
    self.jobs = {}

  def run(self):
    LOG = logging.getLogger("DummySys.drivers.lava.slave")

    # Create the socket
    context = zmq.Context()
    sock =context.socket(zmq.DEALER)
    sock.setsockopt(zmq.IDENTITY, self.hostname)
    sock.setsockopt(zmq.SNDHWM, self.send_queue)
    LOG.info("Connecting to %s as %s", self.master_uri, self.hostname)
    sock.connect(self.master_uri)

    # Create the poller and add the socket
    poller = zmq.Poller()
    poller.register(sock, zmq.POLLIN)

    # Sent the HELLO message, waiting for a reply
    LOG.info("Greating the master")
    sock.send_multipart(["HELLO"])

    while True:
      LOG.info("Waiting for a reply to the 'HELLO'")
      try:
        sockets = dict(poller.poll(self.timeout*1000))
      except zmq.error.ZMQError:
        LOG.debug("Exception raised while waiting")
        continue

      if sockets.get(sock) == zmq.POLLIN:
        msg = sock.recv_multipart()
        LOG.debug("Received from master: %s", msg)
        try:
          action = msg[0]
        except (TypeError, IndexError):
          LOG.error("Invalid message recived from master: %s", msg)
          continue

        if action == "HELLO_OK":
          LOG.info("Connection to master established")
          break

      LOG.debug("Resending an HELLO_RETRY to master")
      sock.send_multipart(["HELLO_RETRY"])

    # Main loop
    while True:
      LOG.info("Waiting for master messages")
      try:
        sockets = dict(poller.poll(self.timeout*1000))
      except zmq.error.ZMQError:
        LOG.debug("Exception raised while waiting")
        continue

      if sockets.get(sock) == zmq.POLLIN:
        msg = sock.recv_multipart()
        LOG.debug("Received from master: %s", msg)
        try:
          action = msg[0]
        except (TypeError, IndexError):
          LOG.error("Invalid message recived from master: %s", msg)

        LOG.debug("Received action=%s, args=(%s)", action, msg[1:])

        if action == "HELLO_OK":
          continue

        elif action == "PONG":
          continue

        elif action == "START":
          try:
            job_id = int(msg[1])
            job_definition = msg[2]
            device_definition = msg[3]
            env = msg[4]
          except (IndexError, ValueError):
              LOG.error("Invalid message '%s'", msg)
              continue
          LOG.info("[%d] Starting job", job_id)
          LOG.debug("[%d]       : %s", job_id, job_definition)
          LOG.debug("[%d] device: %s", job_id, device_definition)
          LOG.debug("[%d] env   : %s", job_id, env)
          #TODO: create a thread that will send back logs

          # Is the job known
          if job_id in self.jobs:
            if self.jobs[job_id].running:
              sock.send_multipart(["START_OK", str(job_id)])
            else:
              sock.send_multipart(["END", str(job_id), "0"])
          else:
            self.jobs[job_id] = Job()
