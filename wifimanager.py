## IMPORTS ##

import sys
import subprocess
import logging
import threading
import os

## COMMON DATA ##

from jjcommon import *

## MODULE GLOBALS ##

_wifimanagerlock = threading.Lock() # locks the wpa_cli resources so they're only used one at a time - if you call while this is being used by another thread, it will block until the lock is freed

_currentwifimode = "unknown" # global storage of current wifi mode

## MODULE FUNCTIONS ##

def getNetworks():
  networks = []
  with _wifimanagerlock:
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
  with _wifimanagerlock:
    if "linux" in sys.platform:
      cp = subprocess.run(["wpa_cli", "-i", iface, "scan"], capture_output=True, text=True)
      if "OK" in cp.stdout:
        cp2 = subprocess.run(["wpa_cli", "-i", iface, "scan_results"], capture_output=True, text=True)
        if cp2.returncode == 0:
          lines = cp2.stdout.strip().split("\n")
          for l in lines:
            if len(l) > 0 and not l.startswith("bssid"):
              parts = l.split(None,4)
              flags = parts[3].strip("[]").split("][")
              if len(parts)==5: # has SSID (4-part entries have blank SSID)
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
  with _wifimanagerlock:
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
  with _wifimanagerlock:
    # add network
    if "linux" in sys.platform:
      cp = subprocess.run(["wpa_cli", "-i", iface, "add_network"], capture_output=True, text=True)
      if cp.returncode == 0:
        netindex = int(cp.stdout.strip())
        logging.debug("netindex={0}".format(netindex))
        allok = True
        cp2 = subprocess.run(["wpa_cli", "-i", iface, "set_network", str(netindex), "ssid", "\""+str(ssid)+"\""], capture_output=True, text=True)
        if "FAIL" in cp2.stdout:
          allok = False
          logging.debug("set ssid fail: " + cp2.stdout)
        cp2 = subprocess.run(["wpa_cli", "-i", iface, "set_network", str(netindex), "psk", "\""+str(psk)+"\""], capture_output=True, text=True)
        if "FAIL" in cp2.stdout:
          allok = False
          logging.debug("set psk fail: " + cp2.stdout)
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
  
def setWifiMode(newwifimode):
  with _wifimanagerlock:
    global _currentwifimode
    if (newwifimode == _currentwifimode):
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

def getWifiMode():
  with _wifimanagerlock:
    thewifimode = _currentwifimode
  return thewifimode