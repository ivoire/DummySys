#!/usr/bin/python

import logging
import time
import zmq


class Driver():
  def __init__(self, conf):
    self.name = "lava-slave"
    self.description = "Lava ZMQ slave"
    self.hostname = conf['hostname']
    self.send_queue = conf['send_queue']
    self.master_uri = conf['master_uri']
    self.log_uri = conf['log_uri']
    self.timeout = conf['timeout']

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

        if action == "HELLO_OK":
          LOG.info("Connection to master established")
          break

      LOG.debug("Resending an HELLO_RETRY to master")
      sock.send_multipart(["HELLO_RETRY"])

    # Main loop
    while True:
