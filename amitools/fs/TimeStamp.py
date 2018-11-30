import time
import os

ts_empty_string = "--.--.---- --:--:--.--"
ts_format = "%d.%m.%Y %H:%M:%S"

class TimeStamp:
  def __init__(self, days=0, mins=0, ticks=0):
    self.days = days
    self.mins = mins
    self.ticks = ticks
    self.secs = (days + 2922) * 24 * 60 * 60 + mins * 60 + (ticks / 50)
    self.sub_secs = (ticks % 50)
  
  def __str__(self):
    t = time.localtime(self.secs)
    ts = time.strftime(ts_format, t)
    return "%s t%02d" % (ts, self.sub_secs)
    
  def get_secsf(self):
    return self.secs + self.sub_secs / 50.0
  
  def get_secs(self):
    return self.secs
  
  def from_secs(self, secs):
    ts   = int(secs)      #entire seconds since epoch
    tmil = secs - ts      #milliseconds
    tmin = ts / 60        #entire minutes
    ts   = ts % 60        #seconds
    tday = tmin / (60*24) #days
    tmin = tmin % (60*24) #minutes
    ts  += tmil           #seconds including milliseconds
    tick = int(ts * 50)   # 1/50 sec
    self.ticks = tick
    self.mins  = tmin
    self.days  = tday - 2922
    self.secs  = secs
    self.sub_secs = (tick % 50)

  def from_path(self, path):
    t = os.path.getmtime(path)
    self.from_secs(t)
  
  def parse(self, s):
    # check for ticks
    s = s.strip()
    ticks = 0
    if len(s) > 3:
      t = s[-3:]
      if t[0] == 't' and t[1:].isdigit():
        ticks = int(t[1:])
        s = s[:-4]
    # parse normal time
    try:
      ts = time.strptime(s, ts_format)
      secs = time.mktime(ts)
      self.from_secs(secs)
      self.sub_secs = ticks
      self.ticks += ticks
      return True
    except ValueError:
      return False
  
if __name__ == '__main__':
  ts = TimeStamp()
  ts.from_secs(123)
  ts2 = TimeStamp(days=ts.days, mins=ts.mins, ticks=ts.ticks)
  if ts2.get_secs() != 123:
    print "FAIL"
  
  ts = TimeStamp()
  s = "05.01.2012 21:47:34 t40"
  ts.parse(s)
  txt = str(ts)
  if s != txt:
    print "FAIL"
  
