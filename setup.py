from setuptools import setup, find_packages

setup(
    name = "dojango",
    version = "svn",
    url = 'http://code.google.com/p/dojango/',
    license = 'License :: OSI Approved :: BSD License',
    description = "Reusable django application that helps you to use the client-side framework dojo",
    author = 'Tobias Klipstein',
    packages = find_packages('.'),
    package_dir = {'': '.'},
    install_requires = ['setuptools'],
    package_data={'': ['*.html']},

)

