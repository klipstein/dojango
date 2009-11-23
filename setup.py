from setuptools import setup, find_packages

setup(
    name = "dojango",
    version = "0.4.5",
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
    packages = find_packages('.'),
    package_dir = {'': '.'},
    install_requires = ['setuptools'],
    package_data={'': ['*.html']},
    zip_safe=False,
)