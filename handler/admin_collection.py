from google.appengine.ext import webapp
from google.appengine.ext.webapp import util as gae_util
from google.appengine.ext.webapp import template
from lp.model import Collection
import os

class AdminCollection(webapp.RequestHandler):
    def get(self):
        result = {}
        
        result['collections'] = Collection.all().fetch(1000)
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template', 'admin_collection.html') #two os.path.dirname to get the root app dir
        self.response.out.write(template.render(template_path, result))
        
    def post(self):
        
        if self.request.get('create'):
            action = 'create'
        elif self.request.get('update'):
            action = 'update'
        elif self.request.get('delete'):
            action = 'delete'
        
        key_names = self.request.get('key_name', allow_multiple=True)
        
        if action == 'create':
            name = self.request.get('new_name')
            slug = self.request.get('new_slug')
            items = [int(id) for id in filter(lambda a: a != '', self.request.get('new_items').strip().split(' '))]
            # list(set(a)) to eliminate duplicates
            # filter to eliminate 2 or more consecutive spaces
            new_collection = Collection(key_name = name, slug = slug, items = items )
            new_collection.put()
            self.redirect('../collection/?status=item_saved')
        elif action == 'update':
            name_list = self.request.get('name', allow_multiple=True)
            slug_list = [ slug for slug in self.request.get('slug', allow_multiple=True)]
            items_list = [[int(id) for id in items.strip().split(' ')] for items in self.request.get('items', allow_multiple=True)]
            collections_list = zip(name_list, slug_list, items_list)
            collections = [Collection(key_name = collection[0], slug = collection[1], items = collection[2]) for collection in collections_list]
            Collection.save(collections)
            self.redirect('../collection/?status=item_saved')
        elif action == 'delete':
            if key_names:
                Collection.delete_by_key_name(key_names)
                self.redirect('../collection/?status=item_deleted')
            else:
                self.redirect('../collection/?status=nothing_selected')
        else:
            # No action specified
            self.redirect('../collection/')

def main():
    application = webapp.WSGIApplication([('/admin/collection/', AdminCollection)],
                                         debug=True)
    gae_util.run_wsgi_app(application)


if __name__ == '__main__':
    main()