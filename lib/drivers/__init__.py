#!/usr/bin/python


def load(parts):
  # TODO: handle errors
  module = __import__(parts)

  for name in parts.split(".")[1:]:
    # TODO: handle errors
    module = getattr(module, name)

  return module
