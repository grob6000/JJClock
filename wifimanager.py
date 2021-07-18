## IMPORTS ##

import sys
import subprocess
import threading
import copy
from time import sleep

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
wifidetailschangedevent = threading.Event()
_changethread = None

# dummy values for when we're testing in windows
_dummynetworks = [{"id":0,"ssid":"dummynetwork_a","connected":True},{"id":1,"ssid":"dummynetwork_b","connected":False}]
_dummyscanresult = [{"bssid":"00:00:00:00","freq":2412,"channel":1,"rssi":-60,"flags":["WPA"],"ssid":"scannetwork_a","id":0},
{"bssid":"00:00:00:00","freq":2437,"channel":6,"rssi":-58,"flags":["WPA"],"ssid":"scannetwork_b","id":1}]

_hostapdconfdefault = {  "interface":jjcommon.iface,
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
  """Convert dictionary into config file text."""
  t = ""
  for k, v in dict.items():
    t += "{0}={1}\n".format(k,v)
  return t

def _parseconftext(t):
  r"""Split config file into dictionary."""
  conf = {}
  t = ""
  for l in t.splitlines():
    if "=" in l:
      kv = l.split("=")
      conf[kv[0]] = kv[1]
  return conf

#def updateDhcpdConf(iface, wifimode):
#  # read from source
#  logger.debug("writing dhcpd.conf for iface={0} mode={1}".format(iface,wifimode))
#  if "linux" in sys.platform:
#    if wifimode in ["ap", "client"]:
#      with open("dhcpcd-"+wifimode+".conf", "r") as f:
#        dhcpcdconf = f.readlines()
#      for l in dhcpcdconf:
#        if l.startswith("interface"):
#          l = "interface " + iface
#      with open("/tmp/dhcpcd.conf", "w") as f:
#        f.writelines(dhcpcdconf)
#      try:
#        subprocess.run(["sudo", "cp", "/tmp/dhcpcd.conf", "/etc/dhcpcd.conf"], check=True)
#      except subprocess.CalledProcessError:
#        logger.error("could not copy dhcpcd.conf")
#    else:
#      logger.warning("bad wifi mode specified: " + wifimode)
#  else:
#    logger.warning("no dhcpcd.conf on this platform")

def readHostapd():
  """Read hostapd.conf file, ensure it's complete (fill with defaults if not) and return dict."""
  conf = {}
  if "linux" in sys.platform:
    try:
      # using cat, because python file read has trouble with file permissions
      hostapdtext = subprocess.run(["cat", "/etc/hostapd/hostapd.conf"], capture_output=True, text=True, check=True)
      conf = _parseconftext(hostapdtext)
    except subprocess.CalledProcessError:
      logger.error("could not read hostapd.conf - using default")
      conf = copy.deepcopy(_hostapdconfdefault)
  else:
    # dummy - return global memory version without reading anything
    logger.warning("no hostapd.conf - returning internal copy only")
    conf = copy.deepcopy(_hostapdconfdefault)
  # ensure whatever is read is complete (fill with defaults)
  changed = False
  for dk, dv in _hostapdconfdefault.items():
    if not dk in conf:
      conf[dk] = dv
      changed = True
  if changed:
    writeHostapd(conf)
  logger.debug("read hostapdconf: " + str(conf))
  return conf

def writeHostapd(conf=None):
  """Write hostapd.conf file."""
  needtochange = False
  if conf:
    global _wifimanagerlock
    with _wifimanagerlock:
      global _currentwifimode
      if "linux" in sys.platform:
        logger.debug("writing hostapdconf: " + str(conf))
        with open("/tmp/hostapd.conf", "w") as f:
          f.write(_makeconftext(conf))
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
    wifidetailschangedevent.set()
    _doAPMode()

def updateHostapd(apssid, appass):
  """Update ssid and password settings in hostapd (no effect if unchanged)."""
  modified = False
  apssid = str(apssid)
  appass = str(appass)
  global _wifimanagerlock
  conf = readHostapd()
  with _wifimanagerlock:
    if not apssid == conf["ssid"]:
      conf["ssid"] = apssid
      modified = True
    if not appass == conf["wpa_passphrase"]:
      conf["wpa_passphrase"] = appass
      modified = True
  if modified:
    writeHostapd(conf)
  else:
    logger.debug("no need to update hostapd; details not changed")


def getChannel(freq):
  """Convert wifi frequency to channel number."""
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
  """Get current wifi client list."""
  networks = []
  iface = settings.getSettingValue("netiface")
  if "linux" in sys.platform:
    # get list of network indices & ssids
    cp = subprocess.run(["wpa_cli", "-i", iface, "list_networks"], capture_output=True, text=True)
    if "FAIL" in cp.stdout:
      logger.error("could not list networks")
    else:
      lines = cp.stdout.splitlines()
      for l in lines:
        if not l.startswith("network id"):
          lsplit = l.split()
          network = {"id":int(lsplit[0]), "ssid":lsplit[1]}
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
            break
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
  """Scan for wifi networks."""
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
  """Remove network from the wifi client list."""
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
  """Add a network to the wifi client list."""
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
          logger.debug("no psk specified; making this an open network")
          cp2 = subprocess.run(["wpa_cli", "-i", iface, "set_network", str(netindex), "key_mgmt", "NONE"], capture_output=True, text=True)
          if "FAIL" in cp2.stdout:
            allok = False
            logger.debug("set key_mgmt fail: " + cp2.stdout)
        cp2 = subprocess.run(["wpa_cli", "-i", iface, "set_network", str(netindex), "ssid", "\""+str(ssid)+"\""], capture_output=True, text=True)
        if "FAIL" in cp2.stdout:
          allok = False
          logger.debug("set ssid fail: " + cp2.stdout)
        cp2 = subprocess.run(["wpa_cli", "-i", iface, "enable_network", str(netindex)], capture_output=True, text=True)
        if "FAIL" in cp2.stdout:
          allok = False
          logger.debug("enable network fail: " + cp2.stdout)
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
  """Change to AP mode - call this in a thread, takes a while."""
  newmode = "unknown"
  iface = settings.getSettingValue("netiface")
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      lp = logpipe.LogPipe(jjlogger.DEBUG, logger)
      badcalls = []
      #cp = subprocess.run(["sudo", "dhclient", iface, "-x"], check=False, stderr=lp, stdout=lp)
      #if not cp.returncode == 0:
      #  badcalls.append("dhclient -x")
      cp = subprocess.run(["wpa_cli", "-i", iface, "disconnect"], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("wpa_cli")
      cp = subprocess.run(["sudo", "ip", "link", "set", "dev", iface, "down"], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("ip link set")
      cp = subprocess.run(["sudo", "ip", "addr", "add", jjcommon.ap_addr+"/25", "dev", iface], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("ip addr add")
      #updateDhcpdConf(iface, "ap")
      cp = subprocess.run(["sudo", "systemctl", "daemon-reload"], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("daemon-reload")
      #cp = subprocess.run(["sudo", "systemctl", "restart", "dhcpcd.service"], check=True, stderr=lp, stdout=lp)
      #if not cp.returncode == 0:
      #  badcalls.append("restart dhcpcd")
      cp = subprocess.run(["sudo", "systemctl", "restart", "dnsmasq.service"], check=True, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("restart dnsmasq")
      cp = subprocess.run(["sudo", "systemctl", "restart", "hostapd.service"], check=True, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("restart hostapd")
      if len(badcalls) == 0:
        newmode = "ap"
        logger.debug("wifi mode succesfully set to ap")
      else:
        logger.error("error when changing to ap mode: " + str(badcalls))
        newmode = "unknown"
      lp.close()
    else:
      logger.warning("cannot change wifi mode")
    global _currentwifimode
    _currentwifimode = newmode
      
def _doClientMode():
  """Change to client mode - call this in a thread; takes a while."""
  newmode = "unknown"
  iface = settings.getSettingValue("netiface")
  global _wifimanagerlock
  with _wifimanagerlock:
    if "linux" in sys.platform:
      lp = logpipe.LogPipe(jjlogger.DEBUG, logger)
      badcalls = []
      cp = subprocess.run(["sudo", "systemctl", "stop", "hostapd.service"], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("stop hostapd")
      cp = subprocess.run(["sudo", "systemctl", "stop", "dnsmasq.service"], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("stop dnsmasq")
      cp = subprocess.run(["sudo", "ip", "link", "set", "dev", iface, "down"], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("ip link down")
      cp = subprocess.run(["sudo", "ip", "addr", "flush", "dev", iface], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("ip addr flush")
      cp = subprocess.run(["wpa_cli", "-i", iface, "reconfigure"], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("wpa_cli reconfigure")
      cp = subprocess.run(["sudo", "systemctl", "daemon-reload"], check=False, stderr=lp, stdout=lp)
      #updateDhcpdConf(iface, "ap")
      if not cp.returncode == 0:
        badcalls.append("daemon-reload")
      cp = subprocess.run(["sudo", "systemctl", "restart", "dhcpcd.service"], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("restart dhcpcd")
      #cp = subprocess.run(["sudo", "dhclient", iface, "-x"], check=False, stderr=lp, stdout=lp)
      #if not cp.returncode == 0:
      #  badcalls.append("dhclient -x")
      cp = subprocess.run(["sudo", "dhclient", iface, "-nw"], check=False, stderr=lp, stdout=lp)
      if not cp.returncode == 0:
        badcalls.append("dhclient")
      if len(badcalls) == 0:
        newmode = "client"
        logger.debug("wifi mode succesfully set to client")
      else:
        newmode = "unknown"
        logger.error("unsuccessful changing to client mode")
      wifidetailschangedevent.set()
      lp.close()
    else:
      logger.warning("cannot change wifi mode")
    global _currentwifimode
    _currentwifimode = newmode

def reconfigureWifi():
  """Asks wpa_cli to reconfigure wifi interface (i.e. reconnect)."""
  if "linux" in sys.platform:
    iface = settings.getSettingValue("netiface")
    global _wifimanagerlock, _currentwifimode
    with _wifimanagerlock:
      if _currentwifimode == "client":
        try:
          subprocess.run(["wpa_cli", "-i", iface, "reconfigure"], check=True)
        except subprocess.CalledProcessError:
          logger.error("unsuccessful reconfiguring wifi")
        else:
          wifidetailschangedevent.set()
      else:
        logger.warning("cannot reconfigure wifi; in AP mode")
  else:
    logger.error("cannot reconfigure wifi")
    
_modechangefuncs = {"ap":_doAPMode, "client":_doClientMode}

def setWifiMode(newwifimode):
  """Set wifi mode to "ap" or "client"."""
  global _wifimanagerlock, _changethread, _targetwifimode, _modechangefuncs, _currentwifimode
  if _changethread and _changethread.is_alive():
    logger.warning("mode change currently in progress. will ignore request to change to " + newwifimode)
  else:
      if _currentwifimode == "changing":
        logger.warning("wifi mode currently changing; request ignored")
      elif (newwifimode == _currentwifimode):
        logger.info("wifi mode unchanged")
      elif newwifimode == "ap" or newwifimode == "client":
        logger.info("wifi mode changing to " + newwifimode)
        with _wifimanagerlock:
          _targetwifimode = newwifimode
          _currentwifimode = "changing"
        _changethread = threading.Thread(target=_modechangefuncs[newwifimode], daemon=True)
        _changethread.start()
      else:
        logger.info("invalid wifi mode, no change")

def getWifiMode():
  """Get current wifi mode, "ap or "client"."""
  global _currentwifimode
  thewifimode = _currentwifimode
  return thewifimode

def checkIfInClientMode():
  """Check wpa_cli and update mode if in client mode (for boot without reconfiguring)."""
  global _currentwifimode
  if not _currentwifimode in ["client", "ap"]:
    wifistatus = getWifiStatus()
    if wifistatus["wpa_state"] == "COMPLETED":
      logger.debug("Assuming wifi in client mode.")
      with _wifimanagerlock:
        _currentwifimode = "client"

def getDHCPDStatus():
  """Get DHCPCD dump"""
  # get dhcpcd dump
  dhcpdstatus = {}
  if "linux" in sys.platform:
    iface = settings.getSettingValue("netiface")
    cp = subprocess.run(["dhcpcd", "-U", iface], capture_output=True, text=True)
    if not "FAIL" in cp.stdout:
      lines = cp.stdout.strip().split("\n")
      for l in lines:
        parts = l.strip().split("=")
        if len(parts)==2:
          dhcpdstatus[parts[0]] = parts[1]
  else:
    logger.warning("cannot retrieve dhcpd status on this platform")
  logger.debug("dhcpdstatus = " + str(dhcpdstatus))
  return dhcpdstatus

def getWifiStatus():
  """Get wifi status using wpa_cli, plus rdns lookup name."""
  wifistatus = {}
  if "linux" in sys.platform:
    global _wifimanagerlock
    iface = settings.getSettingValue("netiface")
    cp = subprocess.run(["wpa_cli", "-i", iface, "status"], capture_output=True, text=True)
    if not "FAIL" in cp.stdout:
      lines = cp.stdout.strip().split("\n")
      for l in lines:
        parts = l.strip().split("=")
        if len(parts)==2:
          wifistatus[parts[0]] = parts[1]
    # rdns lookup for domain name
    if "ip_address" in wifistatus:
      cp = subprocess.run(["nslookup", wifistatus["ip_address"]], capture_output=True, text=True)
      if cp.returncode == 0:
        l = cp.stdout.splitlines()[0] # first entry
        if "name = " in l: # has a name entry
          wifistatus["dnsname"] = l.split("name = ")[1].strip('.')
  else:
    logger.warning("cannot retrieve IP address on this platform")
  logger.debug("wifistatus = " + str(wifistatus))
  return wifistatus

_wifistatusmonitorthread = None
_wifistatusmonitorquit = threading.Event()

def startWifiStatusMonitor():
  """Start monitoring change of wpa_cli status, trigger event on change."""
  global _wifistatusmonitorthread, _wifistatusmonitorquit
  if not (_wifistatusmonitorthread and _wifistatusmonitorthread.is_alive()):
    _wifistatusmonitorquit.clear()
    _wifistatusmonitorthread = threading.Thread(target=_runWifiStatusMonitor, daemon=True)
    _wifistatusmonitorthread.start()

def stopWifiStatusMonitor():
  """Stop monitoring change of wpa_cli status."""
  global _wifistatusmonitorthread, _wifistatusmonitorquit
  if _wifistatusmonitorthread and _wifistatusmonitorthread.is_alive():
    _wifistatusmonitorquit.set()
    _wifistatusmonitorthread.join()

def _runWifiStatusMonitor():
  logger.debug("wifi status monitor started")
  oldwifistatus = {}
  while not _wifistatusmonitorquit.is_set():
    newwifistatus = getWifiStatus()
    for k,v in newwifistatus.items():
      if not (k in oldwifistatus):
        logger.info("{0}={1} added".format(k,v))
        wifidetailschangedevent.set() # something added or changed, send signal
        break # look nae further
      elif not (oldwifistatus[k] == v):
        logger.info("{0} changed from {1} to {2}".format(k,oldwifistatus[k],v))
        wifidetailschangedevent.set() # something added or changed, send signal
        break # look nae further
    oldwifistatus = copy.copy(newwifistatus)
    sleep(2)
  logger.debug("wifi status monitor stopped")

def getWifiInterfaces():
  """Get list of wifi interfaces available using wpa_cli."""
  ifaces = []
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
  """Get device hostname."""
  hostname = None
  if "linux" in sys.platform:
    cp = subprocess.run(["hostname"], capture_output=True, text=True)
    if cp.returncode == 0:
      hostname = cp.stdout.strip()
      logger.debug("hostname: " + hostname)
  else:
    logger.warning("Unable to fetch hostname on this platform")
  return hostname

def setHostname(hostname):
  """Set device hostname."""
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
            #sudo raspi-config nonint do_hostname 
            subprocess.run(["sudo", "raspi-config", "nonint", "do_hostname", hostname], check=True, stderr=lp, stdout=lp)    
          except subprocess.CalledProcessError:
            logger.error("unsuccessful changing hostname")
          else:
            wifidetailschangedevent.set()
          lp.close()
    else:
      logger.warning("cannot change hostname on this platform") 
  