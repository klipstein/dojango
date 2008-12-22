import os
import wsgiref.handlers

from dojango.appengine import memcache_zipserve

from google.appengine.ext import webapp

# setup the environment
from common.appenginepatch.aecmd import setup_env
setup_env(manage_py_env=True)
from dojango.conf import settings

# creating a handler structure for the zip-files within the release folder
release_dir = '%s/release/%s' % (settings.BASE_MEDIA_ROOT, settings.DOJO_VERSION)
handlers = []
for zip_file in os.listdir(release_dir):
    if zip_file.endswith(".zip"):
        module = os.path.splitext(zip_file)[0]
        handler = [os.path.join(release_dir, zip_file)]
        handlers.append(handler)

class FlushCache(webapp.RequestHandler):
    """
    Handler for flushing the whole memcache instance.
    """
    from google.appengine.ext.webapp.util import login_required
    @login_required 
    def get(self):
        from google.appengine.api import memcache
        from google.appengine.api import users
        if users.is_current_user_admin():
            stats = memcache.get_stats()
            memcache.flush_all()
            self.response.out.write("Memcache successfully flushed!<br/>")
            if stats:
                self.response.out.write("<p>Memcache stats:</p><p>")
                for key in stats.keys():
                    self.response.out.write("%s: %s<br/>" % (key, stats[key]))
                self.response.out.write("</p>")

def main():
  application = webapp.WSGIApplication([
      ('%s/%s/(.*)' % (settings.BUILD_MEDIA_URL, settings.DOJO_VERSION),
        memcache_zipserve.create_handler(handlers, max_age=31536000)
      ),
      ('%s/_flushcache[/]{0,1}' % settings.BUILD_MEDIA_URL, FlushCache)
  ], debug=False)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
