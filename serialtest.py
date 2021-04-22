import serial
import datetime
  
def parseNMEA(line):
  fields = line.decode('ascii').split(",")
  cmd = fields[0]
  
  if cmd == "$GPRMC":
    
    hour = int(fields[1][0:2])
    minute = int(fields[1][2:4])
    second = int(fields[1][4:6])
    day = int(fields[9][0:2])
    month = int(fields[9][2:4])
    year = int(fields[9][4:6]) + 2000 
    signalok = bool(fields[2] == "A")
    dt = datetime.datetime(year, month, day, hour, minute, second)
    
    lat = float(fields[3])
    if fields[4] == "S":
      lat = lat * -1
    lng = float(fields[5])
    if fields[6] == "W":
      lng = lng * -1
      
    return {"timestamp":dt,"signalok":signalok,"lat":lat,"lng":lng}
  
  else:
    return {}

ser = serial.Serial('/dev/serial0', 9600)
while (True):
  dt = parseNMEA(ser.readline())
  if "timestamp" in dt:
    print(dt["timestamp"])
  if "signalok" in dt:
    print(dt["signalok"])
  if "lat" in dt and "lng" in dt:
    print("lat={0} lng={1}".format(dt["lat"],dt["lng"]))