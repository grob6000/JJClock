## IMPORTS ##
from PIL import Image, ImageDraw, ImageFont
import os.path #dirname, basename, isfile, join
import glob
import importlib
import sys
import inspect

from renderer import *

## AUTO IMPORT RENDERERS IN THIS DIR ##
renderers = []
pyfiles = glob.glob(os.path.join(os.path.dirname(__file__), "*.py"))
for f in pyfiles:
  if os.path.isfile(f) and not os.path.basename(f).startswith("_"):
    mname = os.path.basename(f)[:-3]
    m = importlib.import_module(mname)
    for c in dir(m):
      if not c.startswith("_"):
        o = getattr(importlib.__import__(mname, globals(), locals(), [c]), c)
        print(o)
        if inspect.isclass(o) and not o==Renderer and issubclass(o, Renderer):
          renderers.append(o)



if __name__ == "__main__":
  
  print("Renderer test routine")
  
  rtotest = []
  if len(sys.argv) == 1:
    rtotest = renderers
  else:
    for r in renderers:
      if r.__name__ in sys.argv[1:]:
        rtotest.append(r)
  
  for r in renderers:
    testRenderer(r)