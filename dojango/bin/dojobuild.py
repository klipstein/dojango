#!/usr/bin/env python
# This is the alternate dojo build command so it can be used
# with older versions of django (mainly because of AppEngine, it uses version 0.96)
import os
import sys
from optparse import OptionParser

def setup_environ():
    # we assume, that dojango is installed within your django's project dir
    project_directory = os.path.abspath(os.path.dirname(__file__)+'/../../')
    settings_filename = "settings.py"
    if not project_directory:
        project_directory = os.getcwd()
    project_name = os.path.basename(project_directory)
    settings_name = os.path.splitext(settings_filename)[0]
    sys.path.append(project_directory)
    sys.path.append(os.path.abspath(project_directory + "/.."))
    project_module = __import__(project_name, {}, {}, [''])
    sys.path.pop()
    # Set DJANGO_SETTINGS_MODULE appropriately.
    os.environ['DJANGO_SETTINGS_MODULE'] = '%s.%s' % (project_name, settings_name)
    return project_directory

project_dir = setup_environ()
from dojango.management.commands.dojobuild import Command

if __name__ == "__main__":
    my_build = Command()
    parser = OptionParser(option_list=my_build.option_list)
    options, args = parser.parse_args(sys.argv)
    my_build.handle(*args[1:], **options.__dict__)