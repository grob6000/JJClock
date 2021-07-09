## IMPORTS ##

import sys
import subprocess
import threading
import copy

## MODULES ##

import jjcommon
import settings
import logpipe
import jjlogger
logger = jjlogger.getLogger(__name__)

## MODULE GLOBALS ##

_wifimanagerlock = threading.Lock() # locks the wpa_cli resources so they're only used one at a time - if you call while this is being used by another thread, it will block until the lock is freed
_currentwifimode = "unknown" # global storage of current wifi mode
_targetwifimode = "unknown" # set for when we run the change routine in the background

# dummy values for when we're testing in windows
_dummynetworks = [{"id":0,"ssid":"dummynetwork_a","connected":True},{"id":1,"ssid":"dummynetwork_b","connected":False}]
_dummyscanresult = [{"bssid":"00:00:00:00","freq":2412,"channel":1,"rssi":-60,"flags":["WPA"],"ssid":"scannetwork_a","id":0},
{"bssid":"00:00:00:00","freq":2437,"channel":6,"rssi":-58,"flags":["WPA"],"ssid":"scannetwork_b","id":1}]

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
        logger.error("could not read hostapd.conf - using default")
        conf = copy.deepcopy(_hostapdconf)
    else:
      # dummy - return global memory version without reading anything
      logger.warning("no hostapd.conf - returning internal copy only")
      conf = copy.deepcopy(_hostapdconf)
  
  logger.debug("read hostapdconf: " + str(_hostapdconf))
  return conf

def writeHostapd():
  needtochange = False
  global _wifimanagerlock
  with _wifimanagerlock:
    global _hostapdconf, _currentwifimode
    logger.debug("writing hostapdconf: " + str(_hostapdconf))
    if "linux" in sys.platform:
      with open("/tmp/hostapd.conf", "w") as f:
        f.write(_makeconftext(_hostapdconf))
      try:
        subprocess.run(["sudo", "cp", "/tmp/hostapd.conf", "/etc/hostapd/hostapd.conf"], check=True)
      except subprocess.CalledProcessError:
        logger.error("could not copy hostapd.conf")
      if _currentwifimode == "ap":
        # restart ap mode
        needtochange = True
    else:
      # dummy - return global memory version without reading anything
      logger.warning("no hostapd.conf - will not write")
  if needtochange:
    _doAPMode()

def updateHostapd(apssid, appass):
  modified = False
  apssid = str(apssid)
  appass = str(appass)
  global _wifimanagerlock
  with _wifimanagerlock:
    global _hostapdconf
    if not apssid == _hostapdconf["ssid"]:
      _hostapdconf["ssid"] = apssid
      modified = True
    if not appass == _hostapdconf["wpa_passphrase"]:
      _hostapdconf["wpa_passphrase"] = appass
      modified = True
  if modified:
    writeHostapd()
  else:
    logger.debug("no need to update hostapd; details not changed")


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
  iface = settings.getSettingValue("netiface")
  global _wifimanagerlock
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
          for n in networks:
            n["connected"] = False
          logger.error("could not get wifi status")
    else:
      logger.error("cannot access wifi config")
      global _dummynetworks
      networks = _dummynetworks
  return networks
  
def scanNetworks(): 
  scannetworks = []
  iface = settings.getSettingValue("netiface")
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
          logger.error("could not retrieve scanned networks")
      else:
        logger.error("could not scan wifi networks")
    else:
      logger.error("cannot access wifi config")
      global _dummyscanresult
      scannetworks = _dummyscanresult
  return scannetworks

def removeNetwork(netindex):
  global _wifimanagerlock
  iface = settings.getSettingValue("netiface")
  with _wifimanagerlock:
    # remove network and save config
    if "linux" in sys.platform:
      cp = subprocess.run(["wpa_cli", "-i", iface, "remove_network", str(netindex)], capture_output=True, text=True)
      if not "OK" in cp.stdout:
        logger.error("could not delete network " + str(netindex))
      cp = subprocess.run(["wpa_cli", "-i", iface, "save_config"], capture_output=True, text=True)
      if not "OK" in cp.stdout:
        logger.error("error saving wifi config")
    else:
      logger.error("cannot access wifi config")
      global _dummynetworks
      for n in _dummynetworks:
        if n["id"] == netindex:
          _dummynetworks.remove(n)
      
  
def addNetwork(ssid, psk=None):
  netindex = -1
  if not ssid or ssid=="":
    return netindex
  iface = settings.getSettingValue("netiface")
  global _wifimanagerlock
  with _wifimanagerlock:
    # add network
    if "linux" in sys.platform:
      cp = subprocess.run(["wpa_cli", "-i", iface, "add_network"], capture_output=True, text=True)
      if cp.returncode == 0:
        netindex = int(cp.stdout.strip())
        logger.debug("netindex={0}".format(netindex))
        allok = True
        cp2 = subprocess.run(["wpa_cli", "-i", iface, "set_network", str(netindex), "ssid", "\""+str(ssid)+"\""], capture_output=True, text=True)
        if "FAIL" in cp2.stdout:
          allok = False
          logger.debug("set ssid fail: " + cp2.stdout)
        if psk:
          cp2 = subprocess.run(["wpa_cli", "-i", iface, "set_network", str(netindex), "psk", "\""+str(psk)+"\""], capture_output=True, text=True)
          if "FAIL" in cp2.stdout:
            allok = False
            logger.debug("set psk fail: " + cp2.stdout)
        else:
          logger.debug("no psk specified; not adding to entry")
        if allok:
          cp = subprocess.run(["wpa_cli", "-i", iface, "save_config"], capture_output=True, text=True)
          if not "OK" in cp.stdout:
            logger.error("error saving wifi config")
        else:
          logger.error("error setting ssid/psk for wifi")
      else:
        logger.error("error adding wifi network")
    else:
      logger.error("cannot access wifi config")
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
  iface = settings.getSettingValue("netiface")
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      lp = logpipe.LogPipe(jjlogger.DEBUG, logger)
      try:
        subprocess.run(["wpa_cli", "-i", iface, "disconnect"], check=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        subprocess.run(["sudo", "ip", "link", "set", "dev", iface, "down"], check=True, stderr=lp, stdout=lp)
        subprocess.run(["sudo", "ip", "addr", "add", jjcommon.ap_addr+"/25", "dev", iface], check=True, stderr=lp, stdout=lp)
        subprocess.run(["sudo", "systemctl", "restart", "dnsmasq.service"], check=True, stderr=lp, stdout=lp)
        subprocess.run(["sudo", "systemctl", "restart", "hostapd.service"], check=True, stderr=lp, stdout=lp)
      except subprocess.CalledProcessError:
        logger.error("unsuccessful changing to ap mode")
      else:
        newmode = "ap"
      lp.close()
    else:
      logger.warning("cannot change wifi mode")
    global _currentwifimode
    _currentwifimode = newmode
  
def _doClientMode():
  newmode = "unknown"
  iface = settings.getSettingValue("netiface")
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      lp = logpipe.LogPipe(jjlogger.DEBUG, logger)
      try:
        subprocess.run(["sudo", "systemctl", "stop", "hostapd.service"], check=True, stderr=lp, stdout=lp)
        subprocess.run(["sudo", "systemctl", "stop", "dnsmasq.service"], check=True, stderr=lp, stdout=lp)
        subprocess.run(["sudo", "ip", "link", "set", "dev", iface, "down"], check=True, stderr=lp, stdout=lp)
        subprocess.run(["sudo", "ip", "addr", "flush", "dev", iface], check=True, stderr=lp, stdout=lp)
        subprocess.run(["wpa_cli", "-i", iface, "reconfigure"], check=True, stderr=lp, stdout=lp)
        subprocess.run(["sudo", "systemctl", "daemon-reload"], check=True, stderr=lp, stdout=lp)
        subprocess.run(["sudo", "systemctl", "restart", "dhcpcd.service"], check=True, stderr=lp, stdout=lp)
        subprocess.run(["sudo", "dhclient", iface], check=True, stderr=lp, stdout=lp)
      except subprocess.CalledProcessError:
        logger.error("unsuccessful changing to client mode")
      else:
        newmode = "client"
      lp.close()
    else:
      logger.warning("cannot change wifi mode")
    global _currentwifimode
    _currentwifimode = newmode  

def reconfigureWifi():
  if "linux" in sys.platform:
    iface = settings.getSettingValue("netiface")
    global _wifimanagerlock
    with _wifimanagerlock:
      global _currentwifimode
      if _currentwifimode == "client":
        try:
          subprocess.run(["wpa_cli", "-i", iface, "reconfigure"], check=True)
        except subprocess.CalledProcessError:
          logger.error("unsuccessful reconfiguring wifi")
      else:
        logger.warning("cannot reconfigure wifi; in AP mode")
  else:
    logger.error("cannot reconfigure wifi")
    
_modechangefuncs = {"ap":_doAPMode, "client":_doClientMode}

def setWifiMode(newwifimode):
  global _wifimanagerlock
  with _wifimanagerlock:
    global _currentwifimode
    if _currentwifimode == "changing":
      logger.warning("wifi mode currently changing; request ignored")
    elif (newwifimode == _currentwifimode):
      logger.info("wifi mode unchanged")
    elif newwifimode == "ap" or newwifimode == "client":
      logger.info("wifi mode changing to " + newwifimode)
      global _targetwifimode
      _targetwifimode = newwifimode
      _currentwifimode = "changing"
      global _modechangefuncs
      t = threading.Thread(target=_modechangefuncs[newwifimode], daemon=False)
      t.start()
    else:
      logger.info("invalid wifi mode, no change")

def getWifiMode():
  global _wifimanagerlock
  with _wifimanagerlock:
    global _currentwifimode
    thewifimode = _currentwifimode
  return thewifimode

def getWifiInterfaces():
  ifaces = []
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      cp = subprocess.run(["wpa_cli", "interface"], capture_output=True, text=True)
      if cp.returncode == 0:
        lines = cp.stdout.splitlines()
        if len(lines) > 2:
          for i in range(2,len(lines)):
            ifaces.append(lines[i])
    else:
      logger.warning("Unable to fetch interfaces on this platform.")
  logger.debug("ifaces found: " + str(ifaces))
  return ifaces

def getHostname():
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      cp = subprocess.run(["hostname"], capture_output=True, text=True)
      if cp.returncode == 0:
        hostname = cp.stdout.strip()
    else:
      logger.warning("Unable to fetch hostname on this platform")
  logger.debug("hostname: " + hostname)
  return hostname

def setHostname(hostname):
  if hostname:
    if "linux" in sys.platform:
      hostname = str(hostname)
      currenthostname = getHostname()
      if hostname == currenthostname:
        logger.debug("hostname already {0}. not changing".format(hostname))
      else:
        logger.debug("setting hostname to: " + hostname)
        global _wifimanagerlock
        with _wifimanagerlock:
          lp = logpipe.LogPipe(jjlogger.DEBUG, logger)
          try:
            subprocess.run(["sudo", "hostname", hostname], check=True, stderr=lp, stdout=lp)    
          except subprocess.CalledProcessError:
            logger.error("unsuccessful changing hostname")
          lp.close()
    else:
      logger.warning("cannot change hostname on this platform") 