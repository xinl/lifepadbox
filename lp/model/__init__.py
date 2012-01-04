from google.appengine.ext import db
import lp.error
import lp.time

import re

class Entry(db.Model):
    #id = 1
    title = db.StringProperty(required = True, default = "(Untitled)", indexed = False)
    published = db.DateTimeProperty()
    updated = db.DateTimeProperty(auto_now = True)
    tags = db.StringListProperty()
    content = db.TextProperty()
    public = db.BooleanProperty() # None = Draft, True = Public, False = Private
    attachments = db.IntegerProperty (default=0, indexed=True)
    
    @classmethod
    def get_by_query(cls, query = {}):
        
        if 'id' in query:
            
            result = [cls.get_by_id(query['id']), ]
            
        else:
            
            q = cls.all()
            
            if 'order' in query:
                q.order(query['order'])
            else:
                q.order("-published")
            
            if 'public' in query:
                q.filter("public = ", query['public'])
            
            if 'tags' in query:
                q.filter("tags IN ", query['tags'])
            
            if 'start_time' in query:
                q.filter("published >= ", lp.time.changetz(query['start_time'], '+0000'))
            
            if  'end_time' in query: 
                q.filter("published < ", lp.time.changetz(query['end_time'], '+0000'))
                
            if 'limit' in query:
                limit = query['limit']
            else:
                limit = 25
            
            if 'page' in query:
                offset = limit * (query['page'] - 1)
            else:
                offset = 0
            
            result = q.fetch(limit, offset)
            total = q.count()
        
        for i in range(len(result)):
            result[i].id = result[i].key().id()
            if 'time_offset' in query:
                result[i].published = lp.time.changetz(result[i].published, query['time_offset'])
        
        if 'id' in query:
            return result[0]
        else:
            return (result, total)
    
    @classmethod
    def save(cls, entries):
        
        if not isinstance(entries, (list, tuple)):
            entries = [entries,]
            
        for i in range(len(entries)):
            
            entries[i].published = lp.time.changetz(entries[i].published, '+0000')
            
            for tag in entries[i].tags:
                if ' ' in tag:
                    raise lp.error.ValidationError("Tag cannot contain spaces.")
            # This is just a safety validation. The Handler should be responsible for the validity of tag string.
            
        return db.put(entries)
    
    @classmethod
    def delete_by_id(cls, ids):
        keys = [db.Key.from_path(cls.kind(), id, parent=None) for id in ids]
        db.delete(keys)
        
    @classmethod
    def delete(cls, models):
        db.delete(models)
    

class Setting(db.Model):
    #key_name = "time_offset"
    value = db.StringProperty (required=False, indexed=False)
  
    KEY_LIST = {
        # Allowed keys and their default values.
        # Don't forget to modify Setting.put() if you change this.
        'remote_publish_protocol': 'aws3',
        'remote_publish_url': '',
        'accept_email_with': '',
        'accept_email_from': '',
        'time_offset': '+0000'
        }
    
    @classmethod
    def get_by_keynames(cls, keynames = None):
        """ Extended from db.Model.get(). Will create a Setting in its default values if key_name is not found.
    
            Args:
                keyname: a string of a key_name, or list of key_names.
    
            Returns:
                a Setting instance or a list of Setting instances. 
        """
        if keynames == None:
            keynames = cls.KEY_LIST.keys()
            
        result = cls.get_by_key_name(keynames)
    
        try: # if iterable
            if None in result: # skip the loop if all key_name are present
                missing = []
                for (offset, key) in enumerate(keynames): #TODO: Possible optimization by converting to list comprehension?
                    if result[offset] == None:
                        result[offset] = Setting(key_name=key, value=cls.KEY_LIST[key])
                        missing.append(result[offset])
                db.put(missing)
        except TypeError: # if not iterable
            #TODO: is kind of braching is hard to understand. Consider revising using isinstance()?
            if result == None:
                result = Setting(key_name=str(keynames), value=cls.KEY_LIST[str(keynames)])
                db.put(result)
          
        return result
  
    @classmethod
    def get_in_dict(cls, keynames = None):
        """
        Extended from Setting.get_by_keynames(). Returns a Dict of key_name / value pairs."""
        # TODO: memcache
        if keynames == None:
            keynames = cls.KEY_LIST.keys()
        result = cls.get_by_keynames(keynames)
        output = {}
    
        try:
            iter(result)
        except TypeError: # if not iterable
            result = [result,]
      
        for item in result:
            output[item.key().name()] = item.value
    
        return output
    
    @classmethod
    def save(cls, settings):
        """ Update or create Setting entries after validating values.
            Note: We don't choose the db.StringProperty(validator = ***) way because there is no way to set a validator to key_name.
    
            Args:
                settings: a Setting object or a list of Setting objects.
            
            Returns:
                a Key object or a List of Key objects of the updated or created entries.
      
            Raise:
                ValidationError: if the provided Setting.value fails to conform the formating rules.
        """
        if not isinstance(settings, (list, tuple)):
            settings = [settings,]
      
        for setting in settings:
      
            keyname = setting.key().name()
      
            if keyname in cls.KEY_LIST:
                #URL check
                if keyname == 'remote_publish_url':
                    if setting.value != '' and not re.match('^(http|https|ftp|file)\://.+', setting.value):
                        raise lp.error.ValidationError("%s is not a valid URL." % setting.value)
                #Email check
                elif keyname == 'accept_email_from' or keyname == 'accept_email_with':
                    for email in setting.value.split(' '):
                        if email != '' and not re.match('^[a-zA-Z][\w\.]+@([\w\-]+\.)+[a-zA-Z]{2,7}$', email):
                            raise lp.error.ValidationError("%s is not a valid email address." % email)
                elif keyname == 'time_offset':
                    if not re.match('^[\+\-][0-9]{4}', setting.value) or int(setting.value[1:3]) > 23 or int(setting.value[3:5]) > 59:
                        raise lp.error.ValidationError("%s is not a valid time zone format. i.e: between -2359 and +2359" % setting.value)
            else: # Drop keynames that are not in KEY_LIST
                settings.remove(setting)
        
        db.put(settings)

class Archive(db.Model):
    #key_name = "201009"
    count = db.IntegerProperty (default=1, indexed=True)
    
class Tag(db.Model):
    #key_name = "Life"
    count = db.IntegerProperty (default=1, indexed=True)
    
class Collection(db.Model):
    #key_name = "Anthology"
    slug = db.StringProperty(required = True)
    items = db.ListProperty(int)
    
    @classmethod
    def save(cls, collections):
        db.put(collections)
    
    @classmethod
    def delete_by_key_name(cls, keynames):
        keys = [db.Key.from_path(cls.kind(), keyname, parent=None) for keyname in keynames]
        db.delete(keys)