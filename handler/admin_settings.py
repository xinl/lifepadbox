from google.appengine.ext import webapp
from google.appengine.ext.webapp import util as gae_util
from google.appengine.ext.webapp import template
from lp.model import Setting
import os

class AdminSettings(webapp.RequestHandler):
    def get(self):
        
        settings = Setting.get_in_dict()
        
        template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'template', 'admin_settings.html') #two os.path.dirname = "../"
        self.response.out.write(template.render(template_path, settings))
        
        
    def post(self):
        
        keynames = Setting.KEY_LIST.keys()
        settings = []
        
        for keyname in keynames:
            settings.append(Setting(key_name=keyname, value=self.request.get(keyname)))
        
        Setting.save(settings)
        
        self.redirect('../?status=settings_saved')


def main():
    application = webapp.WSGIApplication([('/admin/settings/', AdminSettings)],
                                         debug=True)
    gae_util.run_wsgi_app(application)


if __name__ == '__main__':
    main()