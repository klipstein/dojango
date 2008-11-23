from optparse import make_option

import os
import re
import shutil
from dojango.conf import settings

try:
    from django.core.management.base import BaseCommand, CommandError
except ImportError:
    # Fake BaseCommand out so imports on django 0.96 don't fail.
    BaseCommand = object
    class CommandError(Exception):
        pass

class Command(BaseCommand):
    '''This command is used to create your own dojo build. To start a build, you just
    have to type:
    
       ./manage.py dojobuild
    
    in your django project path. With this call, the default build profile "dojango" is used 
    and dojango.profile.js will act as its dojo build configuration. You can also add the 
    option --build_version=dev1.1.1 (for example) to mark the build with it.
    If you want to call a specific build profile from DOJO_BUILD_PROFILES, you just have to 
    append the profile name to this commandline call:
    
       ./manage.py dojobuild profilename
    
    '''
    
    option_list = BaseCommand.option_list + (
        make_option('--build_version', dest='build_version',
            help='Set the version of the build release (e.g. dojango_1.1.1).'),
        make_option('--minify', dest='minify', action="store_true", default=False,
            help='Does a dojo mini build (mainly removing unneeded files (tests/templates/...)'),
        make_option('--minify_extreme', dest='minify_extreme', action="store_true", default=False,
            help='Does a dojo extreme-mini build (keeps only what is defined in build profile and all media files)'),
    )
    help = "Builds a dojo release."
    args = '[dojo build profile name]'
    dojo_base_dir = None
    dojo_release_dir = None
    keep_files = None
    
    def handle(self, *args, **options):
        if len(args)==0:
            # with no param, we use the default profile, that is defined in the settings
            profile_name = settings.DOJO_BUILD_PROFILE
        else:
            profile_name = args[0]
        profile = self._get_profile(profile_name)
        used_src_version = profile['used_src_version'] % {'DOJO_BUILD_VERSION': settings.DOJO_BUILD_VERSION} # no dependencies to project's settings.py file!
        profile_file = os.path.basename(profile['profile_file'] % {'BASE_MEDIA_ROOT':settings.BASE_MEDIA_ROOT})
        # used by minify_extreme!
        self.keep_files = profile.get("minify_extreme_keep_files", None)
        if not self.keep_files:
            self.keep_files = ()
        self.dojo_base_dir = "%(dojo_root)s/%(version)s" % \
                             {'dojo_root':settings.BASE_DOJO_ROOT, 
                             'version':used_src_version}
        # does the defined dojo-directory exist?
        util_base_dir = "%(dojo_base_dir)s/util" % {'dojo_base_dir':self.dojo_base_dir}
        if not os.path.exists(util_base_dir):
            raise CommandError('Put the the dojo source files (version \'%(version)s\') in the folder \'%(folder)s/%(version)s\'' % \
                               {'version':used_src_version,
                                'folder':settings.BASE_DOJO_ROOT})
        # check, if java is installed
        stdin, stdout, stderr = os.popen3(settings.DOJO_BUILD_JAVA_EXEC)
        if stderr.read():
            raise CommandError('Please install java. You need it for building dojo.')
        dest_profile_file = util_base_dir + "/buildscripts/profiles/%(profile_file)s" % \
                            {'profile_file':profile_file}
        # copy the profile to the 
        shutil.copyfile(profile['profile_file'] % {'BASE_MEDIA_ROOT':settings.BASE_MEDIA_ROOT}, dest_profile_file)
        buildscript_dir = os.path.abspath('%s/buildscripts' % util_base_dir)
        if settings.DOJO_BUILD_USED_VERSION < '1.2.0':
            executable = '%(java_exec)s -jar ../shrinksafe/custom_rhino.jar build.js' % \
                         {'java_exec':settings.DOJO_BUILD_JAVA_EXEC}
        else:
            # use the new build command line call!
            if(os.path.sep == "\\"):
                executable = 'build.bat'
            else:
                executable = './build.sh'
        # use the passed version for building
        version = options.get('build_version', None)
        if not version:
            # if no option --build_version was passed, we use the default build version
            version = profile['build_version'] % {'DOJO_BUILD_VERSION': settings.DOJO_BUILD_VERSION} # no dependencies to project's settings.py file!
        # we add the version to our destination base path
        self.dojo_release_dir = '%(base_path)s' % {
                          'base_path':profile['base_root'] % {'BASE_MEDIA_ROOT':settings.BASE_MEDIA_ROOT},} # we don't want to have a dependancy to the project's settings file!
        # the build command handling is so different between the versions!
        # sometimes we need to add /, sometimes not :-(
        # if settings.DOJO_BUILD_USED_VERSION < '1.2.0':
        self.dojo_release_dir = self.dojo_release_dir + os.path.sep
        # setting up the build command
        build_addons = ""
        if settings.DOJO_BUILD_USED_VERSION >= '1.2.0':
            # since version 1.2.0 there is an additional commandline option that does the mini build (solved within js!)
            build_addons = "mini=true"
        exe_command = 'cd %(buildscript_dir)s && %(executable)s version=%(version)s releaseName="%(version)s" releaseDir=%(release_dir)s %(options)s %(build_addons)s' % \
                      {'buildscript_dir':buildscript_dir,
                       'executable':executable,
                       'version':version,
                       'release_dir':self.dojo_release_dir,
                       'options':profile['options'],
                       'build_addons':build_addons}
        # for the minifying process the release_dir is the folder with version included
        self.dojo_release_dir = self.dojo_release_dir + "/" + version
        # print exe_command
        minify = options['minify']
        minify_extreme = options['minify_extreme']
        if settings.DOJO_BUILD_USED_VERSION < '1.2.0' and (minify or minify_extreme):
            self._dojo_mini_before_build()
        # do the build
        os.system(exe_command)
        if settings.DOJO_BUILD_USED_VERSION < '1.2.0':
            if minify or minify_extreme:
                self._dojo_mini_after_build()
        if minify_extreme:
            self._dojo_mini_extreme()
        os.remove(dest_profile_file) # remove the copied profile file
        
    def _get_profile(self, name):
        default_profile_settings = settings.DOJO_BUILD_PROFILES_DEFAULT
        try:
            profile = settings.DOJO_BUILD_PROFILES[name]
            # mixing in the default settings for the build profiles!
            default_profile_settings.update(profile)
            return default_profile_settings
        except KeyError:
            raise CommandError('The profile \'%s\' does not exist in DOJO_BUILD_PROFILES' % name)
        
    def _dojo_mini_before_build(self):
        # FIXME: refs #6616 - could be able to set a global copyright file and null out build_release.txt
        shutil.move("%s/util/buildscripts/copyright.txt" % self.dojo_base_dir, "%s/util/buildscripts/_copyright.txt" % self.dojo_base_dir)
        if not os.path.exists("%s/util/buildscripts/copyright_mini.txt" % self.dojo_base_dir):
            f = open("%s/util/buildscripts/copyright.txt" % self.dojo_base_dir, 'w')
            f.write('''/*
Copyright (c) 2004-2008, The Dojo Foundation All Rights Reserved.
Available via Academic Free License >= 2.1 OR the modified BSD license.
see: http://dojotoolkit.org/license for details
*/''')
            f.close()
        else:
            shutil.copyfile("%s/util/buildscripts/copyright_mini.txt" % self.dojo_base_dir, "%s/util/buildscripts/copyright.txt" % self.dojo_base_dir)
        shutil.move("%s/util/buildscripts/build_notice.txt" % self.dojo_base_dir, "%s/util/buildscripts/_build_notice.txt" % self.dojo_base_dir)
        # create an empty build-notice-file
        f = open("%s/util/buildscripts/build_notice.txt" % self.dojo_base_dir, 'w')
        f.close()
    
    def _dojo_mini_after_build(self):
        try: 
            '''Copied from the build_mini.sh shell script (thank you Pete Higgins :-))'''
            if not os.path.exists(self.dojo_release_dir):
                raise CommandError('The dojo build failed! Check messages above!')
            else:
                # remove dojox tests and demos - they all follow this convetion
                self._remove_files('%s/dojox' % self.dojo_release_dir, ('^tests$', '^demos$'))
                # removed dijit tests
                dijit_tests = ("dijit/tests", "dijit/demos", "dijit/bench", 
                               "dojo/tests", "util",
                               "dijit/themes/themeTesterImages")
                self._remove_folders(dijit_tests)
                # noir isn't worth including yet
                noir_theme_path = ("%s/dijit/themes/noir" % self.dojo_release_dir,)
                self._remove_folders(noir_theme_path)
                # so the themes are there, lets assume that, piggyback on noir: FIXME later
                self._remove_files('%s/dijit/themes' % self.dojo_release_dir, ('^.*\.html$',))
                self._remove_files(self.dojo_release_dir, ('^.*\.uncompressed\.js$',))
                # WARNING: templates have been inlined into the .js -- if you are using dynamic templates,
                # or other build trickery, these lines might not work!
                self._remove_files("dijit/templates", ("^\.html$",))
                self._remove_files("dijit/form/templates", ("^\.html$",))
                self._remove_files("dijit/layout/templates", ("^\.html$",))
                # .. assume you didn't, and clean up all the README's (leaving LICENSE, mind you)
                self._remove_files('%s/dojo/dojox' % self.dojo_release_dir, ('^README$',))
                dojo_folders = ("dojo/_base",)
                self._remove_folders(dojo_folders)
                os.remove("%s/dojo/_base.js" % self.dojo_release_dir)
                os.remove("%s/dojo/build.txt" % self.dojo_release_dir)
                os.remove("%s/dojo/tests.js" % self.dojo_release_dir)
        except Exception, e:
            print e
        # cleanup from above, refs #6616
        shutil.move("%s/util/buildscripts/_copyright.txt" % self.dojo_base_dir, "%s/util/buildscripts/copyright.txt" % self.dojo_base_dir)
        shutil.move("%s/util/buildscripts/_build_notice.txt" % self.dojo_base_dir, "%s/util/buildscripts/build_notice.txt" % self.dojo_base_dir)
        
    def _remove_folders(self, folders):
        for folder in folders:
            if os.path.exists("%s/%s" % (self.dojo_release_dir, folder)):
                shutil.rmtree("%s/%s" % (self.dojo_release_dir, folder))
            
    def _remove_files(self, base_folder, regexp_list):
        for root, dirs, files in os.walk(base_folder):
            for file in files:
                # remove all html-files
                for regexp in regexp_list:
                    my_re = re.compile(regexp)
                    if my_re.match(file):
                        os.remove(os.path.join(root, file))
            for dir in dirs:
                for regexp in regexp_list:
                    my_re = re.compile(regexp)
                    if my_re.match(dir):
                        shutil.rmtree(os.path.join(root, dir))

    EXT_TO_KEEP = (".png", ".gif", ".jpg", ".svg", ".swf", ".fla", ".mov", ".smd",)
    FILES_TO_KEEP = ("xip_client.html", "xip_server.html", "dojo.js",
                     "dojo.xd.js", "iframe_history.html", "blank.html",
                     "dojo.css", "tundra.css", "nihilo.css", "soria.css",)
    FOLDERS_TO_KEEP = ("_firebug", "contrib", "ext-dojo", "filter", "render", "tag", "utils", ) # several folders are needed by dojox.dtl!
    def _dojo_mini_extreme(self):
        """
        This method removes all js files and just leaves all layer dojo files and static files (like "png", "gif", "svg", "swf", ...)
        """
        try:
            '''Copied from the build_mini.sh shell script'''
            if not os.path.exists(self.dojo_release_dir):
                raise CommandError('The dojo build failed! Check messages above!')
            else:
                for root, dirs, files in os.walk(self.dojo_release_dir):
                    for file in files:
                        # remove all html-files
                        my_ext = os.path.splitext(file)[1]
                        my_keep_files = self.FILES_TO_KEEP + self.keep_files
                        if not my_ext in self.EXT_TO_KEEP and not file in my_keep_files and\
                           not os.path.basename(root) in self.FOLDERS_TO_KEEP and os.path.abspath(os.path.join(root, file)).find("/nls/") == -1:
                            os.remove(os.path.join(root, file))
                    for dir in dirs:
                        # special handling for nls folders
                        fullpath = os.path.join(root, dir)
                        # we delete all nls folders of dijit and dojox
                        if dir == "nls" and (fullpath.find("/dijit/") > -1 or fullpath.find("/dojox/") > -1):
                            shutil.rmtree(os.path.join(root, dir))
                # now remove all empty directories
                for root, dirs, files in os.walk(self.dojo_release_dir):
                    for dir in dirs:
                        try:
                            # just empty directories will be removed!
                            os.removedirs(os.path.join(root, dir))
                        except OSError:
                            pass
        except Exception, e:
            print e