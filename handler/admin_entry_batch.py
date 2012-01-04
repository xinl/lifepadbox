from google.appengine.ext import webapp
from google.appengine.ext.webapp import util as gae_util
from google.appengine.ext.webapp import template
from lp.model import Entry
from lp.model import Setting
import lp.stat
import lp.time
import os
import urllib
import math

class AdminEntryBatch(webapp.RequestHandler):
    def get(self):
        path = self.request.path.split('/')[3:] # [3:] cuts off the initial "/admin/entries/"
        settings = Setting.get_in_dict()
        result = {}
        query = {}
        query['time_offset'] = settings['time_offset']
        query['limit'] = 25 # entry per page limit
        
        if path[0] == 'archive':
            result['is_archive'] = True
            year = int(path[1][0:4])
            month = int(path[1][4:6])
            query['start_time'] = lp.time.str2datetime(str(year) + '-' + str(month) + '-01 00:00:00', settings['time_offset'])
            if month == 12:
                month = 1
                year +=1
            else:
                month += 1
            query['end_time'] = lp.time.str2datetime(str(year) + '-' + str(month) + '-01 00:00:00', settings['time_offset'])
        
        elif path[0] == 'tag':
            result['is_tag'] = True
            query['tags'] = urllib.unquote(path[1]).split(' ') #TODO: need to clean the result to avoid injection
            
        elif path[0] == 'draft':
            result['is_draft'] = True
            query['public'] = None
        
        elif path[0] == 'private':
            result['is_private'] = True
            query['public'] = False
        
        if 'page' in path:
            query['page'] = int(path[path.index('page')+1])
        else:
            query['page'] = 1
        
        
        result['query'] = query
        result['entries'], num_entries = Entry.get_by_query(query)
        
        # Setup pagination links
        max_page_links = 7
        num_pages = max(int(math.ceil(num_entries * 1.0 / query['limit'])), 1)
        start_page = max(query['page'] - max_page_links / 2, 2)
        end_page = min(start_page + max_page_links, num_pages)
        
        result['page_list'] = [1, ]
        if start_page > 2:
            result['page_list'] += [0, ]
        result['page_list'] += range(start_page, end_page)
        if end_page < num_pages:
            result['page_list'] += [0, ]
        if num_pages != 1:
            result['page_list'] += [num_pages, ]
        
        result['base_url'] = self.request.path.split('page')[0].rstrip('/')
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template', 'admin_entry_batch.html') #two os.path.dirname to get the root app dir
        self.response.out.write(template.render(template_path, result))
        
    def post(self):
        
        if self.request.get('delete'):
            action = 'delete'
        
        ids = self.request.get('id', allow_multiple=True)
        if action == 'delete':
            if ids:
                ids = [int(id) for id in ids]
                entries = Entry.get_by_id(ids)
                
                substract_archives = []
                substract_terms = []
                for entry in entries:
                    substract_archives += [entry.published.strftime("%Y%m"), ]
                    substract_terms += entry.tags
                if substract_archives:
                    lp.stat.update_count("archive", subtract = substract_archives)
                if substract_terms:
                    lp.stat.update_count("tag", subtract = substract_terms)
                Entry.delete(entries)
                #Entry.delete_by_id(ids)
                self.redirect('../entries/?status=item_deleted')
            else:
                self.redirect('../entries/?status=nothing_selected')
        else:
            # No action specified
            self.redirect('../entries/')

def main():
    application = webapp.WSGIApplication([('/admin/entries/.*', AdminEntryBatch)],
                                         debug=True)
    gae_util.run_wsgi_app(application)


if __name__ == '__main__':
    main()