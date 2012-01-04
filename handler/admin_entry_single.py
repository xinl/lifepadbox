from google.appengine.ext import webapp
from google.appengine.ext.webapp import util as gae_util
from google.appengine.ext.webapp import template
from lp.model import Entry
from lp.model import Setting
import lp.stat
import lp.time
import os
import datetime
import copy

class AdminEntrySingle(webapp.RequestHandler):
    def get(self):
        path = self.request.path.split('/')[3:] # cut off the initial "/admin/entry/"
        settings = Setting.get_in_dict()
        result = {}
        
        id = path[0]
        if id == '':
            # New entry page
            result['is_draft'] = True
        else:
            query = {}
            query['id'] = int(id)
            query['time_offset'] = settings['time_offset']
            
            result['entry'] = Entry.get_by_query(query)
            if result:
                if result['entry'].public == None:
                    result['is_draft'] = True
            else:
                # The id is not valid, go to new entry page.
                self.redirect('../entry/?status=bad_id')
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template', 'admin_entry_single.html') #two os.path.dirname = "../"
        self.response.out.write(template.render(template_path, result))
        
        
    def post(self):
        settings = Setting.get_in_dict()
        
        # getting the entry status and saving action
        is_newentry = (self.request.get('id') == '')
        is_draft = (self.request.get('public') == '')
        if self.request.get('publish'):
            action = 'publish'
        elif self.request.get('saveasdraft'):
            action = 'saveasdraft'
        elif self.request.get('update'):
            action = 'update'
        
        if is_newentry:
            entry = Entry()
        else:
            entry = Entry.get_by_id(int(self.request.get('id')))
            entry_original = copy.deepcopy(entry)#Entry()
            #entry_original.published = entry.published
            #entry_original.tags = entry.tags
        
        if entry:
            if self.request.get('title'):
                entry.title = self.request.get('title')
            entry.content = self.request.get('content')
            
            # setup publish time
            if is_draft:
                entry.published = datetime.datetime.utcnow()
                # Always update publish time when save as draft so the draft will be bumped to the top.
            else:
                entry.published = lp.time.str2datetime(self.request.get('published'), settings['time_offset'])
                # Allow manual edit of published time only on non-draft non-new entries
            
            # setup tags
            if self.request.get('tags'):
                entry.tags = list(set(filter(lambda a: a != '', self.request.get('tags').strip().split(' '))))
                # list(set(a)) to eliminate duplicates
                # filter to eliminate 2 or more consecutive spaces
            else:
                entry.tags = []
            
            #setup entry status and update archives and tags
            if action == 'publish':
                entry.public = True
                lp.stat.update_count("archive", add = [entry.published.strftime("%Y%m"), ] )
                if entry.tags:
                    lp.stat.update_count("tag", add = entry.tags)
            elif action == 'saveasdraft':
                #public = None to indicate a draft post
                entry.public = None
            elif action == 'update':
                # We don't set a publicity until the entry is published.
                entry.public = (self.request.get('public') == 'True')
                if entry.published.strftime("%Y%m") != entry_original.published.strftime("%Y%m"):
                    lp.stat.update_count("archive", add = [entry.published.strftime("%Y%m"), ], subtract = [entry_original.published.strftime("%Y%m"), ])
                if set(entry.tags) != set(entry_original.tags):
                    lp.stat.update_count("tag", add = entry.tags, subtract = entry_original.tags)
            
            Entry.save(entry)
            
            self.redirect('../entries/?status=item_saved')
            
        else:
            
            self.redirect('../entry/?status=bad_id')


def main():
    application = webapp.WSGIApplication([('/admin/entry/.*', AdminEntrySingle)],
                                         debug=True)
    gae_util.run_wsgi_app(application)


if __name__ == '__main__':
    main()