# JJ Clock
# Lots of love from George 2021

## INCLUDES ##
import datetime
import os
import random
import math
import os
import serial
import time
import pytz
import timezonefinder
from PIL import Image, ImageDraw, ImageFont
import sys
from github import Github
import re

if "linux" in sys.platform:
  from gpiozero import Device, Button
  #from gpiozero.pins.mock import MockFactory
  from IT8951.display import AutoEPDDisplay
  from IT8951 import constants
  import pydbus
  import subprocess

# set up logger
import logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

## LOCAL MODULES ##

import jjrenderer
import gpshandler

## CONSTANTS ##

from jjcommon import *

modelist = ["splash","menu","config"]
# load renderers, generate menu
rinstances = {}
for k,r in jjrenderer.renderers.items():
    rinst = r()
    name = rinst.getName()
    rinstances[name] = rinst
    if not name in modelist:
      modelist.append(name)
logging.debug(str(modelist))

# populate menu
menu = [rinstances["config"]]
for k, r in rinstances.items():
  if "clock" in k:
    menu.append(r)

menutimeout = 10 # seconds

## GLOBALS ##
pleasequit = False
currentmode = -1 # initialise as an invalid mode; any mode change will trigger change
currentwifimode = "unknown"
epddisplay = None
menuitemselected = 0
lastsoftwareupdatecheck = 0

# timing
t_lastbuttonpress = 0
menutimeout_armed = False

systzname = "UTC"
tz = pytz.UTC
tf = timezonefinder.TimezoneFinder()
currentdt = datetime.datetime.now()

scriptpath = os.path.dirname(os.path.realpath(sys.argv[0]))
print(scriptpath)

## FUNCTIONS ##

def displayRender(renderer, **kwargs):
  global epddisplay
  global cropbox
  global boxsize
  logging.info("rendering " + renderer.getName())
  screen = Image.new("L", boxsize)
  screen = renderer.doRender(screen,**kwargs)
  if epddisplay:
    epddisplay.frame_buf.paste(screen, (cropbox[0],cropbox[1])) # paste to buffer
    epddisplay.draw_full(constants.DisplayModes.GC16) # display
  else:
    screen.show()
  
def onButton():
  global menuitemselected
  global menu
  global menutimeout_armed
  global t_lastbuttonpress
  global currentmode
  t_lastbuttonpress = time.monotonic()
  logging.info("button pressed, t={0}".format(t_lastbuttonpress))
  if currentmode == "menu":
    menuitemselected = (menuitemselected+1)%len(menu) 
    logging.debug("selected item = " + str(menuitemselected))
    displayRender(rinstances["menu"], menu=menu, selecteditem=menuitemselected)
  else:
    menutimeout_armed = True
    changeMode("menu")

def onMenuTimeout():
  global menuitemselected
  logging.info("menu timeout")
  changeMode(menu[menuitemselected].getName())

def setWifiMode(newwifimode):
  global currentwifimode
  if (newwifimode == currentwifimode):
    logging.info("wifi mode unchanged")
  elif newwifimode == "ap":
    logging.info("wifi mode AP")
    try:
      subprocess.run(["bash", os.path.join(scriptpath, "apmode.sh")], check=True)
    except subprocess.CalledProcessError:
      logging.error("unsuccessful running apmode.sh")
    currentwifimode = newwifimode
  elif newwifimode == "client":
    logging.info("wifi mode Client")
    try:
      subprocess.run(["bash", os.path.join(scriptpath, "clientmode.sh")], check=True)
    except subprocess.CalledProcessError:
      logging.error("unsuccessful running clientmode.sh")
    currentwifimode = newwifimode
  else:
    logging.info("invalid wifi mode, no change")

def savePersistentMode(mode):
  logging.info("NOT IMPLEMENTED - persist mode as file")

def loadPersistentMode():
  return "clock_digital" # default for now
  logging.info("NOT IMPLEMENTED - load persistent mode from file")

def formatIP(ip):
  return "{ip[0]}.{ip[1]}.{ip[2]}.{ip[3]}".format(ip=ip)
  
def changeMode(mode):
  global modelist
  global currentmode
  global renderers
  global menuitemselected
  global menu
  r = None
  kwargs = {"mode":mode}
  if mode in modelist and not mode == currentmode:
    logging.info("changing mode to " + mode)
    currentmode = mode
    if mode == "config":
      # set wifi to AP mode
      setWifiMode("ap")
      gpsstat = gpshandler.getStatus()
      kwargs["ssid"] = ap_ssid
      kwargs["password"] = ap_pass
      kwargs["ip"] = formatIP(ip_addr)
      kwargs["gpsstat"] = gpsstat
    else:
      setWifiMode("client") # all other modes should be in client state (if no wifi configured, will be disconnected...)
    if mode == "menu":
        kwargs["selecteditem"] = menuitemselected
        kwargs["menu"] = menu
    if mode in rinstances:
      r = rinstances[mode]
      kwargs["timestamp"] = currentdt
    else:
      r = jjrenderer.Renderer()
    savePersistentMode(mode)
    displayRender(r,**kwargs)
  else:
    logging.warning("invalid mode " + mode + " - not changing")
  
def updateTime(dt):
  global currentdt
  #global renderers
  #global currentmode
  currentdt = dt
  #print(dt)
  ui = rinstances[currentmode].getUpdateInterval()
  if (dt.second == 0) and ("clock" in currentmode) and (currentmode in rinstances) and ((dt.minute + dt.hour*60) % ui == 0):
    displayRender(rinstances[currentmode], timestamp=dt, mode=currentmode)

def setSystemTz(tzname):
  if not tzname == systzname:
    if "linux" in sys.platform:
      logging.info("updating system timezone")
      r = subprocess.run(["sudo","timedatectl","set-timezone",tzname])
      if r.returncode == 0:
        logging.info("success - system timezone changed to " + getSystemTz())
    else:
      systzname = tzname
      logging.warning("non-linux os: cannot update system timezone. dummy value set to " + systzname)

def getSystemTz():
  if "linux" in sys.platform:
    return pydbus.SystemBus().get(".timedate1").Timezone
  else:
    logging.warning("cannot access system timezone. returning dummy.")
    return systzname

def checkForUpdate():
  global lastupdate
  
  logging.warning("not implemented - check for update")
  
  g = Github(githubtoken)
  repo = g.get_repo(githubrepo)
  rels = repo.get_releases()
  latestpub = datetime.datetime.min
  for r in rels:
    if r.published_at > latestpub:
      latestpub = r.published_at
      latestrel = r
  wgeturl = latestrel.tarball_url
  tag = latestrel.tag_name
  
  # get the current tag of the repo
  myname = ""
  if "linux" in sys.platform:
    try:
      myname = subprocess.run(["git", "describe", "--tags", "--abbrev=0"], text=True, capture_output=True).stdout.strip()
    except subprocess.CalledProcessError:
      logging.warning("unknown version. will update.")
  
  lastsoftwareupdatecheck = time.monotonic()
  
  if myname == tag:
    logging.info("currently latest version. no update required.")
  else:
    logging.info("current version: " + myname + ", available: " + tag)
    doUpdate(wgeturl, tag)
    
  return wgeturl, tag

def doUpdate(wgeturl, tag):

  updateok = True
  logging.info("updating now...")
  if "linux" in sys.platform:
    
    # display an updating screen
    displayRender(jjrenderer.renderers["RendererUpdating"], version=tag)
    
    # make sure temp dir exists
    subprocess.run(["mkdir", "/tmp/jjclock"])
    
    # copy update script to temp location
    try:
      subprocess.run(["cp", os.path.join(scriptpath, "update.sh"), updatetempfile], check=True)
    except subprocess.CalledProcessError:
      logging.error("could not move update script")
      updateok = False     
      
    try:
      subprocess.Popen(["bash", updatetempfile])
    except subprocess.CalledProcessError:
      logging.error("problem starting update script")
      updateok = False
  
  # quit if all went well  
  if updateok:
    quit()

examplenetwork = {"index":0,"ssid":"examplessid","psk":"password123","bssid":"00:11:22:33:44:55", "frequency":"2462", "rssi":-71, "flags":["WPA2-PSK-CCMP","ESS"]}

def getNetworks():
  networks = []
  if "linux" in sys.platform:
    for i in range(0,10): # why would anyone configure more than 10???? yes magic numbers well whoopdeedoo
      cp = subprocess.run(["wpa_cli", "-i", iface, "get_network", str(i), "ssid"], capture_output=True, text=True)
      if "FAIL" in cp.stdout:
        break
      else:
        network = {"id":i, "ssid":cp.stdout.strip('" \n')}
        # for now, don't need anything else
        networks.append(network)
  else:
    logging.error("cannot access wifi config")
  return networks
    
def scanNetworks():
  scannetworks = []
  if "linux" in sys.platform:
    cp = subprocess.run(["wpa_cli", "-i", iface, "scan"], capture_output=True, text=True)
    if "OK" in cp.stdout:
      cp2 = subprocess.run(["wpa_cli", "-i", iface, "scan_results"], capture_output=True, text=True)
      if cp2.returncode == 0:
        lines = cp2.stdout.split("\n")
        for l in lines:
          if not l.startswith("bssid"):
            parts = re.split('\s', l, maxsplit=4)
            flags = parts[3].strip("[]").split("][")
            network = {"bssid":parts[0],"freq":int(parts[1]),"rssi":int(parts[2]),"flags":flags,"ssid":parts[4]}
            scannetworks.append(network)
      else:
        logging.error("could not retrieve scanned networks")
    else:
      logging.error("could not scan wifi networks")
  else:
    logging.error("cannot access wifi config")
  return scannetworks

def removeNetwork(netindex):
  # remove network and save config
  if "linux" in sys.platform:
    cp = subprocess.run(["wpa_cli", "-i", iface, "remove_network", str(netindex)], capture_output=True, text=True)
    if not "OK" in cp.stdout:
      logging.error("could not delete network " + str(netindex))
    cp = subprocess.run(["wpa_cli", "-i", iface, "save_config"], capture_output=True, text=True)
    if not "OK" in cp.stdout:
      logging.error("error saving wifi config")
  else:
    logging.error("cannot access wifi config")
    
def addNetwork(ssid, psk):
  netindex = -1
  # add network
  if "linux" in sys.platform:
    cp = subprocess.run(["wpa_cli", "-i", iface, "add_network"], capture_output=True, text=True)
    if cp.returncode == 0:
      netindex = int(cp.stdout.strip())
      allok = True
      cp2 = subprocess.run(["wpa_cli", "-i", iface, "set_network", str(netindex), "ssid", "'\""+str(ssid)+"\"'"], capture_output=True, text=True)
      if "FAIL" in cp2.stdout:
        allok = False
      cp2 = subprocess.run(["wpa_cli", "-i", iface, "set_network", str(netindex), "psk", "'\""+str(psk)+"\"'"], capture_output=True, text=True)
      if "FAIL" in cp2.stdout:
        allok = False
      if allok:
        cp = subprocess.run(["wpa_cli", "-i", iface, "save_config"], capture_output=True, text=True)
        if not "OK" in cp.stdout:
          logging.error("error saving wifi config")
      else:
        logging.error("error setting ssid/psk for wifi")
    else:
      logging.error("error adding wifi network")
  else:
    logging.error("cannot access wifi config")
  return netindex
    
## SCRIPT ##
if __name__ == "__main__":

  # init gpio
  if "linux" in sys.platform:
    logging.info("init gpio")
    #Device.pin_factory = MockFactory()
    userbutton = Button(buttongpio, bounce_time=debounce/1000.0)
    userbutton.when_pressed = onButton
  else:
    logging.warning("GPIO not available on this platform, no button enabled.")
  
  # init epd display
  if "linux" in sys.platform:
    logging.info("init display")
    epddisplay = AutoEPDDisplay(vcom=display_vcom)
  else:
    logging.warning("no display on this platform.")
    epddisplay = None
  
  
  # wifi setup
  #logging.debug(getNetworks())

  # now screen is running, check for update
  #checkForUpdate()

  # wifi testing
  n = getNetworks()
  print(n)
  
  sn = scanNetworks()
  print(sn)
  
  i = addNetwork("test", "nobigdeal")
  n = getNetworks()
  print(n)
  
  removeNetwork(i)
  n = getNetworks()
  print(n)
  
  quit()
  
  # splash
  #changeMode("splash")
  #time.sleep(2)
  
  # load system timezone
  systzname = getSystemTz()
  tz = pytz.timezone(systzname)
  
  # load last mode
  changeMode(loadPersistentMode())
  
  # gps serial
  gpshandler = gpshandler.GpsHandler() # create and start gps handler
  gpshandler.connect()
  
  tlastupdate = time.monotonic()
  while not pleasequit:
      
      t = time.monotonic()
      if menutimeout_armed and t - t_lastbuttonpress > menutimeout:
        menutimeout_armed = False
        onMenuTimeout()
      
      # if NMEA has been received, update the time
      if gpshandler.pollUpdated():
        stat = gpshandler.getStatus()
        if stat["hastime"]:
          if stat["tz"]:
            dt = gpshandler.getDateTime(local=True)
            p = "using nmea time + tz: "
            # update timezone cached
            if not tz == stat["tz"]:
              tz = stat["tz"]
              # update system timezone
              if not getSystemTz() == tz.zone:
                setSystemTz(tz.zone)
          else:
            dt = gpshandler.getDateTime(local=False).astimezone(tz)
            p = "using nmea time + cached tz: "
        else:
          dt = datetime.datetime.now()
          p = "using system time: "
        if dt:
          logging.debug(p + dt.strftime("%H:%M:%S %z"))
          updateTime(dt)
          t = time.monotonic()
          if t-lastsoftwareupdatecheck > minupdateinterval:
            if dt.hour == updatehour or t-lastsoftwareupdatecheck > maxupdateinterval:
              checkForUpdate()
      else:
        t = time.monotonic()
        if ((t - tlastupdate) >= 2):
          tlastupdate = t
          updateTime(datetime.datetime.now())
          
      time.sleep(0.2) # limit to 5Hz
  
  # Close the window and quit.
  logging.info("quitting")
