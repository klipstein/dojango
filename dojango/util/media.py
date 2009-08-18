from django.conf import settings
from dojango.conf import settings as dojango_settings
from django.core.exceptions import ImproperlyConfigured
from django.utils._os import safe_join
from django.conf.urls.defaults import patterns
from os import path, listdir

def find_app_dir(app_name):
    """Given an app name (from settings.INSTALLED_APPS) return the abspath
    to that app directory"""
    i = app_name.rfind('.')
    if i == -1:
        m, a = app_name, None
    else:
        m, a = app_name[:i], app_name[i+1:]
    try:
        if a is None:
            mod = __import__(m, {}, {}, [])
        else:
            mod = getattr(__import__(m, {}, {}, [a]), a)
        return path.dirname(path.abspath(mod.__file__))
    except ImportError, e:
        raise ImproperlyConfigured, 'ImportError %s: %s' % (app_name, e.args[0])

def find_app_dojo_dir(app_name):
    """Checks, if a dojo-media directory exists within a given app and returns the absolute path to it."""
    base = find_app_dir(app_name)
    if base:
        media_dir = safe_join(base, 'dojo-media')
        if path.isdir(media_dir): return media_dir
    return None # no dojo-media directory was found within that app

def find_app_dojo_dir_and_url(app_name):
    """Returns a list of tuples of dojo modules within an apps 'dojo-media' directory.
    Each tuple contains the abspath to the module directory and the module name.
    """
    ret = []
    media_dir = find_app_dojo_dir(app_name)
    if not media_dir: return None
    for d in listdir(media_dir):
        if path.isdir(safe_join(media_dir, d)):
            if d not in ("src", "release") and not d.startswith("."):
                ret.append(tuple([safe_join(media_dir, d), "%(module)s" % {
                    'module': d
                }]))
    return tuple(ret)

dojo_media_library = dict((app, find_app_dojo_dir_and_url(app))
                         for app in settings.INSTALLED_APPS)
dojo_media_apps = tuple(app for app in settings.INSTALLED_APPS
                       if dojo_media_library[app])

def _check_app_dojo_dirs():
    """Checks, that each dojo module is just present once. Otherwise it would throw an error."""
    check = {}
    for app in dojo_media_apps:
        root_and_urls = dojo_media_library[app]
        for elem in root_and_urls:
            root, url = elem
            if url in check and root != dojo_media_library[check[url]][0]:
                raise ImproperlyConfigured, (
                    "Two apps (%s, %s) contain the same dojo module (%s) in the dojo-media-directory pointing to two different directories (%s, %s)" %
                    (repr(app), repr(check[url]), repr(root.split("/")[-1]), repr(root), repr(dojo_media_library[check[url]][0][0])))
            check[url] = app

def _build_urlmap():
    """Creating a url map for all dojo modules (dojo-media directory), that are available within activated apps."""
    seen = {}
    valid_urls = [] # keep the order!
    for app in dojo_media_apps:
        root_and_urls = dojo_media_library[app]
        for elem in root_and_urls:
            root, url = elem
            if url.startswith('/'): url = url[1:]
            if url in seen: continue
            valid_urls.append((url, root))
            seen[url] = root
    base_url = dojango_settings.DOJO_MEDIA_URL # dojango_settings.BASE_MEDIA_URL
    if base_url.startswith('/'): base_url = base_url[1:]
    # all new modules need to be available next to dojo, so we need to allow a version-string in between
    # e.g. /dojo-media/1.3.1/mydojonamespace == /dojo-media/1.2.0/mydojonamespace
    valid_urls = [("%(base_url)s/([\w\d\.\-]*/)?%(url)s" % {
        'base_url': base_url,
        'url': m[0]
    }, m[1]) for m in valid_urls]
    
    valid_urls.append(("%(base_url)s/release/" % {'base_url': base_url}, path.join(dojango_settings.BASE_MEDIA_ROOT, "release")))
    valid_urls.append(("%(base_url)s/" % {'base_url': base_url}, path.join(dojango_settings.BASE_MEDIA_ROOT, "src")))
    return valid_urls

_check_app_dojo_dirs() # is each dojo module just created once?

dojo_media_urls = _build_urlmap()
urls = [ ('^%s(?P<path>.*)$' % url, 'serve', {'document_root': root, 'show_indexes': True} )
         for url, root in dojo_media_urls ]
url_patterns = patterns('django.views.static', *urls) # url_patterns that can be used directly within urls.py