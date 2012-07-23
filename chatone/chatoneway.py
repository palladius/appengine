from google.appengine.ext             import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import datetime

class WelcomePage(webapp.RequestHandler):
  def get(self):
    page_title = 'ChatOneWay v3'
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write(
      """<html>
          <head>
            <title>%s</title>
            <META HTTP-EQUIV="refresh" CONTENT="2; URL=http://www.htmlgoodies.com/tutors/refresh.html">
          </head>
         <body>
         <h1>Welcome to %s</h1>
         
	<p>Current time (bis): %s</p>
	<p>(refresh every 5 min)</p>
         </body>
      </html>""" % ( page_title, page_title, datetime.datetime.now() )
    )

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Hello, webapp World!')

#chatapp = webapp.WSGIApplication( [('/', MainPage)], debug=True)
chatapp = webapp.WSGIApplication( [('/', WelcomePage)] )

def main():
    run_wsgi_app(chatapp)

if __name__ == "__main__":
    main()
