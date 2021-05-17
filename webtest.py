import webadmin
import time
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

print("Testing webadmin...")

wa = webadmin.WebAdmin()
wa.start()

networks = [{"ssid":"bubbles","id_str":"1","psk":"abcde"}]
wa.provideWifiNetworks(networks)

n = 0
while True:
  action = wa.getActionData()
  if action:
    for k, v in action.items():
      print("{0:32} | {1}".format(k,v))
  time.sleep(1)
  n=n+1

wa.stop()