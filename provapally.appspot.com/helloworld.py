
# https://developers.google.com/appengine/docs/python/gettingstarted/usingusers

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import jinja2
import os

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)))

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()

        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('[ProvaPally]: Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))

application = webapp.WSGIApplication(
                                     [('/', MainPage)],
                                     debug=True)


def main():
    #run_wsgi_app(application)
    template = jinja_environment.get_template(
    'index.html')
    self.response.write(template.render())


if __name__ == "__main__":
    main()


