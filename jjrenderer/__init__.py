## IMPORTS ##
from PIL import Image, ImageDraw, ImageFont
import os.path #dirname, basename, isfile, join
import glob
import importlib
import inspect
import logging

from jjrenderer.renderer import *

## AUTO IMPORT RENDERERS IN THIS DIR ##
pyfiles = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
for f in pyfiles:
  if os.path.isfile(f) and not os.path.basename(f).startswith("_"):
    mname = os.path.basename(f)[:-3]
    m = importlib.import_module("." + mname, "jjrenderer")
    for c in dir(m):
      if not c.startswith("_"):
        o = getattr(importlib.__import__("jjrenderer." + mname, globals(), locals(), [c]), c)
        #print(o)
        if inspect.isclass(o) and not o==Renderer and issubclass(o, Renderer):
          renderers[o.name]=o
logging.debug("renderers = " + str(renderers))