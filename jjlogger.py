import logging
import sys

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
FATAL = logging.FATAL

# create a top level logger
logger = logging.getLogger("jjclock")
formatter = logging.Formatter('%(asctime)-12s %(name)-20s %(levelname)-8s %(message)s', '%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
logger.handlers.clear()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.propagate = False

# get a child
def getLogger(name=None):
  global logger, handler
  if not name or name == "":
    return logger
  else:
    childlog = logger.getChild(name)
    return childlog

def subsumeLogger(logger=None):
  global handler
  if logger:
    lo = None
    if isinstance(logger, str):
      lo = logging.getLogger(logger)
    if isinstance(logger, logging.Logger):
      lo = logger
  if lo:
    lo.propagate = False
    for h in lo.handlers:
      lo.removeHandler(h)
    lo.addHandler(handler)
