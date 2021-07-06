import logging
import sys

DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL
FATAL = logging.FATAL
levels = {"DEBUG":DEBUG, "INFO":INFO, "WARNING":WARNING, "ERROR":ERROR, "CRITICAL":CRITICAL, "FATAL":FATAL}

# create a top level logger
logger = logging.getLogger("jjclock")
formatter = logging.Formatter('%(levelname)s : %(name)s : %(message)s')
handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(formatter)
logger.handlers.clear()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG) # default is everything
logger.propagate = False

# known loggers
knownloggers = {"jjclock"}

# set logging level
def setLogLevel(level):
  if isinstance(level, str) and level in levels.keys():
    level = levels[level]
  level = int(level)
  if not level == logger.level:
    for lname in knownloggers:
      logging.getLogger(lname).setLevel(level)
      logging.info("Set log level to: " + str(level))

# get a child
def getLogger(name=None):
  global logger, handler
  if not name or name == "":
    return logger
  else:
    childlog = logger.getChild(name)
    knownloggers.add(childlog.name)
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
    knownloggers.add(lo.name)
