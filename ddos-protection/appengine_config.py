
# copied from colleague:
# https://github.com/scotch/operation_curl_block/blob/master/appengine_config.py

from webob import Response

class AntiCurlMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ['HTTP_USER_AGENT'].startswith('curl'):
            resp = Response('Too many requests!')
            resp.status = 429
            return resp(environ, start_response)
        return self.app(environ, start_response)

def webapp_add_wsgi_middleware(app):
    return AntiCurlMiddleware(app)

