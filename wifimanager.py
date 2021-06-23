## IMPORTS ##

import sys
import subprocess
import logging
import threading
import copy

## COMMON DATA ##

import jjcommon

## MODULE GLOBALS ##

_wifimanagerlock = threading.Lock() # locks the wpa_cli resources so they're only used one at a time - if you call while this is being used by another thread, it will block until the lock is freed
_currentmodelock = threading.Lock() # lock for the current wifi mode variable
_currentwifimode = "unknown" # global storage of current wifi mode
_targetwifimode = "unknown" # set for when we run the change routine in the background

# dummy values for when we're testing in windows
_dummynetworks = [{"id":0,"ssid":"dummynetwork_a","connected":True},{"id":1,"ssid":"dummynetwork_b","connected":False}]
_dummyscanresult = [{"bssid":"00:00:00:00","freq":2412,"channel":1,"rssi":-60,"flags":["WPA"],"ssid":"scannetwork_a","id":0},
{"bssid":"00:00:00:00","freq":2437,"channel":6,"rssi":-58,"flags":["WPA"],"ssid":"scannetwork_b","id":1}]

# ap ssid and password to use
#_apssid = jjcommon.ap_ssid
#_appass = jjcommon.ap_pass

_hostapdconf = {  "interface":jjcommon.iface,
                  "ssid":jjcommon.ap_ssid,
                  "hw_mode":"g",
                  "channel":"6",
                  "macaddr_acl":"0",
                  "auth_algs":"1",
                  "ignore_broadcast_ssid":"0",
                  "wpa":"2",
                  "wpa_passphrase":jjcommon.ap_pass,
                  "wpa_key_mgmt":"WPA-PSK",
                  "wpa_pairwise":"TKIP",
                  "rsn_pairwise":"CCMP", }

def _makeconftext(dict):
  t = ""
  for k, v in dict.items():
    t += "{0}={1}\n".format(k,v)
  return t

def _parseconftext(t):
  conf = {}
  t = ""
  for l in t.splitlines():
    if "=" in l:
      kv = l.split("=")
      conf[kv[0]] = kv[1]
  return conf

def readHostapd():
  conf = {}
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      try:
        hostapdtext = subprocess.run(["cat", "/etc/hostapd/hostapd.conf"], capture_output=True, text=True, check=True)
        conf = _parseconftext(hostapdtext)
      except subprocess.CalledProcessError:
        logging.error("could not read hostapd.conf - using default")
        conf = copy.deepcopy(_hostapdconf)
    else:
      # dummy - return global memory version without reading anything
      logging.warning("no hostapd.conf - returning internal copy only")
      conf = copy.deepcopy(_hostapdconf)
  
  logging.debug("read hostapdconf: " + str(_hostapdconf))
  return conf

def writeHostapd():
  needtochange = False
  global _wifimanagerlock
  with _wifimanagerlock:
    global _hostapdconf, _currentwifimode
    logging.debug("writing hostapdconf: " + str(_hostapdconf))
    if "linux" in sys.platform:
      with open("/tmp/hostapd.conf", "w") as f:
        f.write(_makeconftext(_hostapdconf))
      try:
        subprocess.run(["sudo", "cp", "/tmp/hostapd.conf", "/etc/hostapd/hostapd.conf"], check=True)
      except subprocess.CalledProcessError:
        logging.error("could not copy hostapd.conf")
      if _currentwifimode == "ap":
        # restart ap mode
        needtochange = True
    else:
      # dummy - return global memory version without reading anything
      logging.warning("no hostapd.conf - will not write")
  if needtochange:
    _doAPMode()

def updateHostapd(settings):
  modified = False
  global _wifimanagerlock
  with _wifimanagerlock:
    global _hostapdconf
    if "apssid" in settings:
      v = settings["apssid"].getValue()
      if not v == _hostapdconf["ssid"]:
        _hostapdconf["ssid"] = v
        modified = True
    if "appass" in settings:
      v = settings["appass"].getValue()
      if not v == _hostapdconf["wpa_passphrase"]:
        _hostapdconf["wpa_passphrase"] = v
        modified = True
  if modified:
    writeHostapd()


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
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      for i in range(0,10): # why would anyone configure more than 10???? yes magic numbers well whoopdeedoo
        cp = subprocess.run(["wpa_cli", "-i", jjcommon.iface, "get_network", str(i), "ssid"], capture_output=True, text=True)
        if "FAIL" in cp.stdout:
          break
        else:
          network = {"id":i, "ssid":cp.stdout.strip('" \n')}
          # for now, don't need anything else
          networks.append(network)
        cp = subprocess.run(["wpa_cli", "-i", jjcommon.iface, "status"], capture_output=True, text=True)
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
      global _dummynetworks
      networks = _dummynetworks
  return networks
  
def scanNetworks(): 
  scannetworks = []
  global _wifimanagerlock
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
      global _dummyscanresult
      scannetworks = _dummyscanresult
  return scannetworks

def removeNetwork(netindex):
  global _wifimanagerlock
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
      global _dummynetworks
      for n in _dummynetworks:
        if n["id"] == netindex:
          _dummynetworks.remove(n)
      
  
def addNetwork(ssid, psk=None):
  netindex = -1
  if not ssid or ssid=="":
    return netindex
  
  global _wifimanagerlock
  with _wifimanagerlock:
    # add network
    if "linux" in sys.platform:
      cp = subprocess.run(["wpa_cli", "-i", jjcommon.iface, "add_network"], capture_output=True, text=True)
      if cp.returncode == 0:
        netindex = int(cp.stdout.strip())
        logging.debug("netindex={0}".format(netindex))
        allok = True
        cp2 = subprocess.run(["wpa_cli", "-i", jjcommon.iface, "set_network", str(netindex), "ssid", "\""+str(ssid)+"\""], capture_output=True, text=True)
        if "FAIL" in cp2.stdout:
          allok = False
          logging.debug("set ssid fail: " + cp2.stdout)
        if psk:
          cp2 = subprocess.run(["wpa_cli", "-i", jjcommon.iface, "set_network", str(netindex), "psk", "\""+str(psk)+"\""], capture_output=True, text=True)
          if "FAIL" in cp2.stdout:
            allok = False
            logging.debug("set psk fail: " + cp2.stdout)
        else:
          logging.debug("no psk specified; not adding to entry")
        if allok:
          cp = subprocess.run(["wpa_cli", "-i", jjcommon.iface, "save_config"], capture_output=True, text=True)
          if not "OK" in cp.stdout:
            logging.error("error saving wifi config")
        else:
          logging.error("error setting ssid/psk for wifi")
      else:
        logging.error("error adding wifi network")
    else:
      logging.error("cannot access wifi config")
      indexused = []
      global _dummynetworks
      for n in _dummynetworks:
        indexused.append(n["id"])
      for i in range(0,20):
        if not i in indexused:
          netindex = i
          _dummynetworks.append({"id":i, "ssid":ssid, "connected":False})
          break
      
  return netindex

def _doAPMode():
  newmode = "unknown"
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      try:
        subprocess.run(["wpa_cli", "-i", jjcommon.iface, "disconnect"], check=True)
        subprocess.run(["sudo", "ip", "link", "set", "dev", jjcommon.iface, "down"], check=True)
        subprocess.run(["sudo", "ip", "addr", "add", jjcommon.ap_addr+"/25", "dev", jjcommon.iface], check=True)
        subprocess.run(["sudo", "systemctl", "restart", "dnsmasq.service"], check=True)
        subprocess.run(["sudo", "systemctl", "restart", "hostapd.service"], check=True)
      except subprocess.CalledProcessError:
        logging.error("unsuccessful changing to ap mode")
      else:
        newmode = "ap"
    else:
      logging.warning("cannot change wifi mode")
    global _currentwifimode
    _currentwifimode = newmode
  
def _doClientMode():
  newmode = "unknown"
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      try:
        subprocess.run(["sudo", "systemctl", "stop", "hostapd.service"], check=True)
        subprocess.run(["sudo", "systemctl", "stop", "dnsmasq.service"], check=True)
        subprocess.run(["sudo", "ip", "link", "set", "dev", jjcommon.iface, "down"], check=True)
        subprocess.run(["sudo", "ip", "addr", "flush", "dev", jjcommon.iface], check=True)
        subprocess.run(["wpa_cli", "-i", jjcommon.iface, "reconfigure"], check=True)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True)
        subprocess.run(["sudo", "systemctl", "restart", "dhcpcd.service"], check=True)
        subprocess.run(["sudo", "dhclient", jjcommon.iface], check=True)
      except subprocess.CalledProcessError:
        logging.error("unsuccessful changing to client mode")
      else:
        newmode = "client"
    else:
      logging.warning("cannot change wifi mode")
    global _currentwifimode
    _currentwifimode = newmode  

def reconfigureWifi():
  if "linux" in sys.platform:
    global _wifimanagerlock
    with _wifimanagerlock:
      global _currentwifimode
      if _currentwifimode == "client":
        try:
          subprocess.run(["wpa_cli", "-i", jjcommon.iface, "reconfigure"], check=True)
        except subprocess.CalledProcessError:
          logging.error("unsuccessful reconfiguring wifi")
      else:
        logging.warning("cannot reconfigure wifi; in AP mode")
  else:
    logging.error("cannot reconfigure wifi")
    
_modechangefuncs = {"ap":_doAPMode, "client":_doClientMode}

def setWifiMode(newwifimode):
  global _wifimanagerlock
  with _wifimanagerlock:
    global _currentwifimode
    if _currentwifimode == "changing":
      logging.warning("wifi mode currently changing; request ignored")
    elif (newwifimode == _currentwifimode):
      logging.info("wifi mode unchanged")
    elif newwifimode == "ap" or newwifimode == "client":
      logging.info("wifi mode changing to " + newwifimode)
      global _targetwifimode
      _targetwifimode = newwifimode
      _currentwifimode = "changing"
      global _modechangefuncs
      t = threading.Thread(target=_modechangefuncs[newwifimode], daemon=False)
      t.start()
    else:
      logging.info("invalid wifi mode, no change")

def getWifiMode():
  global _wifimanagerlock
  with _wifimanagerlock:
    global _currentwifimode
    thewifimode = _currentwifimode
  return thewifimode