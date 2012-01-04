from django.utils import simplejson
import datetime
#import re
from google.appengine.ext import db
from google.appengine.api import users

from lp.model import Entry

# A solution from http://stackoverflow.com/questions/1531501/json-serialization-of-google-app-engine-models/3063649#3063649
# To decode date in javascript:
# function decodeJsonDate(s){
#  return new Date(s.slice(0,19).replace('T',' ')+' GMT');
#}
class _GAEModelEncoder(simplejson.JSONEncoder):
    def default(self, obj):
        isa=lambda *xs: any(isinstance(obj, x) for x in xs) # shortcut
        
        if isa(datetime.datetime):
            obj = obj.replace(microsecond = 0)
            # No need to expose microsecond to the end user.
            return obj.isoformat()
        elif isa(db.Model):
            result = dict((p, getattr(obj, p)) for p in obj.properties())
            """
            if isa(Entry):
                obj.content = re.sub(r'\r\n|\r|\n', '<br />', obj.content)
                # Replace newlines with <br />
            """
            if isa(Entry):
                result.pop("attachments")
                result.pop("public")
                result['id'] = obj.key().id()
            return result
        elif isa(users.User):
            return obj.email()
        else:
            return simplejson.JSONEncoder.default(self, obj)
        
        """ # The original L33T version:
        return obj.isoformat() if isa(datetime.datetime) else \
        dict((p, getattr(obj, p)) for p in obj.properties()) if isa(db.Model) else \
        obj.email() if isa(users.User) else \
        simplejson.JSONEncoder.default(self, obj)
        """

def encode(obj):
    return simplejson.dumps(obj, cls=_GAEModelEncoder, ensure_ascii=False)

def encodep(obj):
    # A versatile static solution to jsonp from http://kawanet.blogspot.com/2008/01/jsonp-se-jsonp-static-emulation.html
    # pre = "(function(d){var l=document.getElementsByTagName('script');var t=l[0].src.match(/[\?\&]callback=([A-Za-z0-9\_\.\[\]]*)/);var f=t?t[1]:'callback';eval(f+'(d)');})("
    pre = "lp_jsonp("
    end = ");"
    return pre + simplejson.dumps(obj, cls=_GAEModelEncoder, ensure_ascii=False, separators=(',',':')) + end
