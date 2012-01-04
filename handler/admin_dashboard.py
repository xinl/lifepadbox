from google.appengine.ext import webapp
from google.appengine.ext.webapp import util as gae_util
from google.appengine.ext.webapp import template
import os

from lp.model import Entry
import lp.json

class AdminDashboard(webapp.RequestHandler):
    def get(self):
        
        result = {}
        
        entries, num_entries = Entry.get_by_query()
        
        result['json'] = lp.json.encodep(entries)
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template', 'admin_dashboard.html') #two os.path.dirname = "../"
        self.response.out.write(template.render(template_path, result))
        
        
    def post(self):
        
        pass


def main():
    application = webapp.WSGIApplication([('/admin/', AdminDashboard)],
                                         debug=True)
    gae_util.run_wsgi_app(application)


if __name__ == '__main__':
    main()