#!/usr/bin/env python

import webapp2

class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('Hello world (Riccardo @ Provapally)!')

app = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
