import serial
import datetime
import timezonefinder
import pytz

def parseNMEA(line):
  fields = line.decode('ascii').split(",")
  cmd = fields[0]
  data = {}
  
  if cmd == "$GPRMC":
    
    hour = int(fields[1][0:2])
    minute = int(fields[1][2:4])
    second = int(fields[1][4:6])
    day = int(fields[9][0:2])
    month = int(fields[9][2:4])
    year = int(fields[9][4:6]) + 2000 
    data["timestamp"] = datetime.datetime(year, month, day, hour, minute, second)

    data["signalok"] = bool(fields[2] == "A")
    
    if len(fields[3])>0:
      lat = float(fields[3][0:2]) + float(fields[3][2:])/60
      if fields[4] == "S":
        lat = lat * -1
      data["lat"] = lat
      
    if len(fields[5])>0:
      lng = float(fields[5][0:3]) + float(fields[5][3:])/60
      if fields[6] == "W":
        lng = lng * -1
      data["lng"] = lng
      
  return data

ser = serial.Serial('/dev/serial0', 9600)
tf = timezonefinder.TimezoneFinder()

while (True):
  d = parseNMEA(ser.readline())
  if "timestamp" in d:
    print(d["timestamp"])
  if "signalok" in d:
    print(d["signalok"])
  if "lat" in dt and "lng" in dt:
    tzname = tf.certain_timezone_at(lat=d["lat"],lng=d["lng"])
    tz = pytz.timezone(tzname)
    localtime = tz.localize(d["timestamp"])
    print("lat={0} lng={1} tz={2} localtime={3}".format(d["lat"],d["lng"],tzname,localtime))
    
    