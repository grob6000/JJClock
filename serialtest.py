import serial
import datetime
import timezonefinder
import pytz
import subprocess

systzname = ""
tz = pytz.UTC

def parseNMEA(line):

  global tz
  global systzname
  
  print(line)
  fields = line.decode('ascii').split(",")
  cmd = fields[0]
  data = {}
  
  if cmd == "$GPRMC":
    
    # utc time
    hour = int(fields[1][0:2])
    minute = int(fields[1][2:4])
    second = int(fields[1][4:6])
    day = int(fields[9][0:2])
    month = int(fields[9][2:4])
    year = int(fields[9][4:6]) + 2000 
    data["timestamp"] = datetime.datetime(year, month, day, hour, minute, second, tzinfo=pytz.UTC)

    # signal validity
    data["signalok"] = bool(fields[2] == "A")
    
    # lat and lng
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

    # timezone - check 1/min if all preconditions met
    if second == 0 and data["signalok"] and "lat" in data and "lng" in data:
      tzname = tf.certain_timezone_at(lat=data["lat"],lng=data["lng"])
      tz = pytz.timezone(tzname)
      if not tzname == systzname:
        # TO-DO update system timezone
        print("update system timezone")
        r = subprocess.run(["sudo","timedatectl","set-timezone",tzname])
        if r.returncode == 0:
          systzname = tzname
          print("success")
    # local time
    data["localtime"] = data["timestamp"].astimezone(tz)
    
  return data

ser = serial.Serial('/dev/serial0', 9600)
tf = timezonefinder.TimezoneFinder()

while (True):
  d = parseNMEA(ser.readline())
  if "timestamp" in d:
    print(d["timestamp"])
  if "signalok" in d:
    print(d["signalok"])
  if "lat" in d and "lng" in d:
    tzname = tf.certain_timezone_at(lat=d["lat"],lng=d["lng"])
    tz = pytz.timezone(tzname)
    localtime = d["timestamp"].astimezone(tz)
    print("lat={0} lng={1} tz={2} localtime={3}".format(d["lat"],d["lng"],tz,localtime))
    
    