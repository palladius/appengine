#!/usr/bin/env python

# 2.7

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import webapp2
import jinja2
import os

#class MainHandler(webapp2.RequestHandler):
#    def get(self):
#        self.response.out.write('Hello world (Riccardo @ Provapally)!')

#app = webapp2.WSGIApplication([('/', MainHandler)], debug=True)

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write('[ProvaPally Obsolete]: Hello, ' + user.nickname())
        else:
            self.redirect(users.create_login_url(self.request.uri))

app = webapp.WSGIApplication( [('/', MainPage)], debug=True )

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        os.path.dirname(__file__)))