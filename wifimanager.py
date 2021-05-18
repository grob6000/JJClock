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

_dummynetworks = [{"id":0,"ssid":"dummynetwork_a","connected":True},{"id":1,"ssid":"dummynetwork_b","connected":False}]
_dummyscanresult = [{"bssid":"00:00:00:00","freq":2412,"channel":1,"rssi":-60,"flags":["WPA"],"ssid":"scannetwork_a","id":0},
{"bssid":"00:00:00:00","freq":2437,"channel":6,"rssi":-58,"flags":["WPA"],"ssid":"scannetwork_b","id":1}]

def getChannel(freq):
  if 2412 <= freq <= 2472:
    return int((freq - 2412)/5)+1
  elif freq == 2484:
    return 14
  elif 4915 <= freq <= 4980:
    return int((freq-4915)/5)+183
  elif 5035 <= freq <= 5885:
    return int((freq - 5035)/5)+7
  else:
    return 0

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
        cp = subprocess.run(["wpa_cli", "-i", iface, "status"], capture_output=True, text=True)
        if not "FAIL" in cp.stdout:
          lines = cp.stdout.strip().split("\n")
          for l in lines:
            parts = l.strip().split("=")
            if len(parts)==2 and parts[0]=="id":
              connectedid = int(parts[1])
              for n in networks:
                n["connected"] = bool(n["id"] == connectedid)
        else:
          logging.error("could not get wifi status")
    else:
      logging.error("cannot access wifi config")
      networks = _dummynetworks
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
          i = 0
          for l in lines:
            if len(l) > 0 and not l.startswith("bssid"):
              parts = l.split(None,4)
              flags = parts[3].strip("[]").split("][")
              if len(parts)==5: # has SSID (4-part entries have blank SSID)
                network = {"bssid":parts[0],"freq":int(parts[1]),"rssi":int(parts[2]),"flags":flags,"ssid":parts[4],"id":i}
                network["channel"] = getChannel(network["freq"])
                scannetworks.append(network)
                i = i + 1
        else:
          logging.error("could not retrieve scanned networks")
      else:
        logging.error("could not scan wifi networks")
    else:
      logging.error("cannot access wifi config")
      scannetworks = _dummyscanresult
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
      for n in _dummynetworks:
        if n["id"] == netindex:
          _dummynetworks.remove(n)
      
  
def addNetwork(ssid, psk=None):
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
        if psk:
          cp2 = subprocess.run(["wpa_cli", "-i", iface, "set_network", str(netindex), "psk", "\""+str(psk)+"\""], capture_output=True, text=True)
          if "FAIL" in cp2.stdout:
            allok = False
            logging.debug("set psk fail: " + cp2.stdout)
        else:
          logging.debug("no psk specified; not adding to entry")
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
      indexused = []
      for n in _dummynetworks:
        indexused.append(n["id"])
      for i in range(0,20):
        if not i in indexused:
          netindex = i
          _dummynetworks.append({"id":i, "ssid":ssid, "connected":False})
          break
      
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