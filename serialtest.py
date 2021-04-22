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
    return {"timestamp":dt,"signalok":signalok}
  else:
    return {}

ser = serial.Serial('/dev/serial0', 9600)
while (True):
  dt = parseNMEA(ser.readline())
  if "timestamp" in dt:
    print dt["timestamp"]
  if "signalok" in dt:
    print dt["signalok"]