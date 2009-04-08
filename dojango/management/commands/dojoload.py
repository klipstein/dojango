import os
import sys
import urllib
import zipfile

from optparse import make_option
from dojango.conf import settings

try:
    from django.core.management.base import BaseCommand, CommandError
except ImportError:
    # Fake BaseCommand out so imports on django 0.96 don't fail.
    BaseCommand = object
    class CommandError(Exception):
        pass

class Command(BaseCommand):
    '''This command helps with downloading a dojo source release. To download 
    the currently defined 'settings.DOJANGO_DOJO_VERSION' just type:

       ./manage.py dojoload

    in your django project path. For downloading a specific version a version 
    string can be appended.

       ./manage.py dojoload --version 1.2.3
    '''

    option_list = BaseCommand.option_list + (
        make_option('--dojo_version', dest='dojo_version',
            help='Download a defined version (e.g. 1.2.3) instead of the default (%s).' % settings.DOJO_VERSION),
    )
    help = "Downloads a dojo source release."
    dl_url = "http://download.dojotoolkit.org/release-%(version)s/dojo-release-%(version)s-src.zip"
    dl_to_path = settings.BASE_DOJO_ROOT + "/dojo-release-%(version)s-src.zip"
    move_from_dir = settings.BASE_DOJO_ROOT + "/dojo-release-%(version)s-src"
    move_to_dir = settings.BASE_DOJO_ROOT + "/%(version)s"
    extract_to_dir = settings.BASE_DOJO_ROOT
    total_kb = 0
    downloaded_kb = 0


    def handle(self, *args, **options):
        version = settings.DOJO_VERSION
        passed_version = options.get('dojo_version', None)
        if passed_version:
            version = passed_version
        dl_url = self.dl_url % {'version': version}
        dl_to_path = self.dl_to_path % {'version': version}
        move_from_dir = self.move_from_dir % {'version': version}
        move_to_dir = self.move_to_dir % {'version': version}
        if os.path.exists(move_to_dir):
            raise CommandError("You've already downloaded version %(version)s to %(move_to_dir)s" % {
                'version':version,
                'move_to_dir':move_to_dir,
            })
        else:
            print "Downloading %s to %s" % (dl_url, dl_to_path)
            self.download(dl_url, dl_to_path)
            if self.total_kb == -1: # stupid bug in urllib (there is no IOError thrown, when a 404 occurs
                os.remove(dl_to_path)
                print ""
                raise CommandError("There is no source release at %(url)s" % {
                    'url':dl_url,
                    'dir':dl_to_path,
                })
            print "\nExtracting file %s to %s" % (dl_to_path, move_to_dir)
            self.unzip_file_into_dir(dl_to_path, self.extract_to_dir)
            os.rename(move_from_dir, move_to_dir)
            print "Removing previous downloaded file %s" % dl_to_path
            os.remove(dl_to_path)

    def download(self, dl_url, to_dir):
        try:
            urllib.urlretrieve(dl_url, to_dir, self.dl_reporthook)
        except IOError:
            raise CommandError("Downloading from %(url)s to directory %(dir)s failed." % {
                'url':dl_url,
                'dir':to_dir,
            })

    def dl_reporthook(self, block_count, block_size, total_size):
        self.total_kb = total_size / 1024
        self.downloaded_kb = (block_count * block_size) / 1024
        sys.stdout.write('%s%d KB of %d KB downloaded' % (
                40*"\b", # replacing the current line
                self.downloaded_kb,
                self.total_kb
            )
        )
        sys.stdout.flush()

    def unzip_file_into_dir(self, file, dir):
        try:
            os.mkdir(dir)
        except:
            pass
        zfobj = zipfile.ZipFile(file)
        for name in zfobj.namelist():
            if name.endswith('/'):
                os.mkdir(os.path.join(dir, name))
            else:
                outfile = open(os.path.join(dir, name), 'wb')
                outfile.write(zfobj.read(name))
                outfile.close()
