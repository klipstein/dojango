from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES
import os
import sys

# COPIED FROM SETUP.PY OF DJANGO
def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)

# Tell distutils to put the data_files in platform-specific installation
# locations. See here for an explanation:
# http://groups.google.com/group/comp.lang.python/browse_thread/thread/35ec7b2fed36eaec/2105ee4d9e8042cb
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
dojango_dir = 'dojango'

for dirpath, dirnames, filenames in os.walk(dojango_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        data_files.append([dirpath, [os.path.join(dirpath, f) for f in filenames]])

# Small hack for working with bdist_wininst.
# See http://mail.python.org/pipermail/distutils-sig/2004-August/004134.html
if len(sys.argv) > 1 and sys.argv[1] == 'bdist_wininst':
    for file_info in data_files:
        file_info[0] = '\\PURELIB\\%s' % file_info[0]

# Dynamically calculate the version based on dojango.VERSION.
version = __import__('dojango').get_version()
if u'SVN' in version:
    version = ' '.join(version.split(' ')[:-1])


setup(
    name = "dojango",
    version = version,
    url = 'http://code.google.com/p/dojango/',
    license = 'License :: OSI Approved :: BSD License',
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Environment :: Web Environment",
    ],
    description = 'Reusable django application that helps you to use the client-side framework dojo',
    keywords = 'dojo,django,dojango,javascript',
    author = 'Tobias von Klipstein',
    author_email='tk@uxebu.com',
    packages = packages,
    data_files = data_files,
)