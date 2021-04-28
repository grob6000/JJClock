# common definitions and constants

# display & rendering
screensize = (1448, 1072) # Set the width and height of the screen [width, height]
display_vcom = -2.55 # v - as per cable
cropbox = (10,10,1410,1060) # area we should work within / x1, y1, x2, y2
boxsize = (cropbox[2]-cropbox[0],cropbox[3]-cropbox[1]) # x,y
clx = int((cropbox[2] + cropbox[0])/2)
cly = int((cropbox[3] + cropbox[1])/2)

# gpio
buttongpio = 23
debounce = 50 #ms

# wifi
iface = "wlan0"
ap_ssid = "JJClockSetup"
ap_pass = "12071983"
ip_addr = (192,168,99,1)
ip_mask = (255,255,255,0)
dhcp_start = (192,168,99,10)
dhcp_end = (192,168,99,20)