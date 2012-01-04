import datetime

class TZOffset(datetime.tzinfo):
    def __init__(self, offset_string):
        # validity of offset_string is already taken care of by Setting.put() so we just trust it here. 
        self.offset_string = offset_string
        self._h = int(self.offset_string[1:3])
        self._m = int(self.offset_string[3:5])
        if self.offset_string[0] == "-":
            self._h = - self._h
            self._m = - self._m
    
    def utcoffset(self, dt): return datetime.timedelta(hours = self._h, minutes = self._m)
    
    def dst(self, dt): return datetime.timedelta(0)
    
    def tzname(self, dt): return self.offset_string

#UTC = TZOffset("+0000")

def str2datetime(time_str, time_zone="+0000"):
    """ Convert string (format: YYYY-MM-DD HH:MM:SS) into datetime object. """
    # For some unknown reason, datetime.strptime() refuse to work.
    ts = time_str.split(' ')
    ts[0] = ts[0].split('-')
    ts[1] = ts[1].split(':')
    time_object = datetime.datetime(int(ts[0][0]), int(ts[0][1]), int(ts[0][2]), int(ts[1][0]), int(ts[1][1]), int(ts[1][2]), 000000, TZOffset(time_zone))
    
    #time_object = datetime.datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S')
    #time_object.tzinfo = TZOffset(time_zone)
    return time_object

def datetime2str(time_obj):
    """ Convert datetime object to string (format: YYYY-MM-DD HH:MM:SS). """
    #time_str = time_obj.strftime("%Y-%m-%d %H:%M:%S")
    time_str = "-".join([str(time_obj.year), str(time_obj.month), str(time_obj.day)]) + " " + ":".join([str(time_obj.hour), str(time_obj.minute), str(time_obj.second)])
    return time_str

def changetz(time_object, timezone_string):
    if time_object.tzinfo == None:
        time_object = time_object.replace(tzinfo=TZOffset("+0000"))
    return time_object.astimezone(TZOffset(timezone_string))
    