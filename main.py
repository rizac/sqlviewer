# encoding: utf-8
'''
main -- shortdesc

main is a description

It defines classes_and_methods

@author:     user_name

@copyright:  2016 organization_name. All rights reserved.

@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter
import threading
import webbrowser
from app import app
from core import set_chache_address
# import random

__all__ = []
__version__ = 0.1
__date__ = '2016-12-02'
__updated__ = '2016-12-02'

DEBUG = 1
TESTRUN = 0
PROFILE = 0


class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg

    def __str__(self):
        return self.msg

    def __unicode__(self):
        return self.msg


def main(argv=None): # IGNORE:C0111
    '''Command line options.'''

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by Riccardo Zaccarelli on %s.
  Copyright 2016. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
#         parser.add_argument("-r", "--recursive", dest="recurse", action="store_true", help="recurse into subfolders [default: %(default)s]")
#         parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]")
#         parser.add_argument("-i", "--include", dest="include", help="only include paths matching this regex pattern. Note: exclude is given preference over include. [default: %(default)s]", metavar="RE" )
#         parser.add_argument("-e", "--exclude", dest="exclude", help="exclude paths matching this regex pattern. [default: %(default)s]", metavar="RE" )
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-D', '--debug', action='store_true')
        parser.add_argument(dest="dburl",
                            help=("The database url in the form: "
                                  "dialect://username:password@host:port/database . "
                                  "E.g.: postgresql://scott:tiger@localhost/mydb "
                                  "(for sqlite: sqlite:///path. "
                                  "E.g.: sqlite:////home/data/db.sqlite"),
                            metavar="dburl",
                            nargs="?")

        # Process arguments
        args = parser.parse_args()
        if args.dburl:
            # http://stackoverflow.com/questions/19277280/preserving-global-state-in-a-flask-application
            set_chache_address(args.dburl)
        #app.run()
        run_in_browser(debug=args.debug)
        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2


def run_in_browser(debug=False):
    port = 5473  # 5000 + random.randint(0, 999)
    url = "http://127.0.0.1:{0}".format(port)
    threading.Timer(4 if debug else 1.25, lambda: webbrowser.open(url)).start()
    app.run(port=port, debug=debug)  # , use_reloader=False)


if __name__ == "__main__":
#     if DEBUG:
#         sys.argv.append("-h")
#         sys.argv.append("-v")
#         sys.argv.append("-r")
#     if TESTRUN:
#         import doctest
#         doctest.testmod()
#     if PROFILE:
#         import cProfile
#         import pstats
#         profile_filename = 'main_profile.txt'
#         cProfile.run('main()', profile_filename)
#         statsfile = open("profile_stats.txt", "wb")
#         p = pstats.Stats(profile_filename, stream=statsfile)
#         stats = p.strip_dirs().sort_stats('cumulative')
#         stats.print_stats()
#         statsfile.close()
#         sys.exit(0)
    sys.exit(main())