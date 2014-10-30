#!/usr/bin/env python
# Updates the binary changelogs, version numbers, hash, and branch from CHANGELOG
# Run and commit changes to git before building release
import os
import re
import subprocess
import sys

CHANGELOG = "CHANGELOG"

re_base = r'(?<=%s)([0-9a-zA-Z._+-]+)'

# [filename, preceding string]
VERSION_FILES = [
    ["scripts/create_release_wiki_table.py", r'VT_VERSION = [\'"]'],
    ["scripts/create_release_wiki_table.py", r'SF_FOLDER_NAME = [\'"]v'], # a second pass
    ["vistrails/core/system/__init__.py", r'VERSION = [\'"]'],
    ["dist/mac/setup.py", r'VERSION = [\'"]'],
    ["dist/windows/vistrails.iss", r'AppVerName=VisTrails '],
    ["dist/windows/vistrailsx64.iss", r'AppVerName=VisTrails x64 '],
    ["dist/windows/custom/vistrails-gdal.iss", r'AppVerName=VisTrails '],
    ["dist/windows/custom/vistrailsx64-gdal.iss", r'AppVerName=VisTrails x64 '],
    ["dist/source/make-vistrails-src-release.py", r'VT_VERSION = [\'"]'],
    ["doc/usersguide/conf.py", r'release = [\'"]'],
    ["dist/common/splash/splash.svg", r'tspan4025">'],
    ["dist/common/splash/splash.svg", r'tspan4025-7">']] # second pass for shadow

HASH_FILES = [["scripts/create_release_wiki_table.py", r'VT_REVISION = [\'"]'],
              ["vistrails/core/system/__init__.py", r'RELEASE = [\'"]'],
              ["dist/source/make-vistrails-src-release.py", r'VT_HASH = [\'"]']]

BRANCH_FILES = [ # For places that should not use 'v' prefix
   ["doc/usersguide/conf.py", r'version = [\'"]']]

BRANCH_FILES_V = [
   ["dist/source/make-vistrails-src-release.py", r'VT_BRANCH = [\'"]']]

BRANCH_URLS = [ # For places that should use dev for master
   ["scripts/get_usersguide.py", r'http://www.vistrails.org/usersguide/']]

def update_value(fname, pre, value):
    """
    fname: file name
    rexp: regular expression to search for
    value: new value

    """
    rexp = re.compile(re_base % pre)

    with open(fname, 'rb') as fp:
        lines = fp.readlines()

    i = 0
    replaced = False
    while i < len(lines):
        line = lines[i]
        m = rexp.search(line)
        if m is not None:
            lines[i] = rexp.sub(value, line)
            print fname, '---', lines[i],
            replaced = True
            break
        i += 1

    if not replaced:
        sys.stderr.write(fname + ": Didn't find version number to replace\n")
        sys.exit(1)

    with open(fname, 'wb') as fp:
        for line in lines:
            fp.write(line)

if __name__ == '__main__':
    os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))

    # Read CHANGELOG
    with open(CHANGELOG, 'rb') as fp:
        lines = fp.readlines()

    # Get info from CHANGELOG
    # Assumes 3:rd line and fixed format
    line = lines[2].split()
    VERSION = line[2][1:] # Drop "v" prefix
    HASH = line[4]
    BRANCH = line[6]
 
    try:
        hash = subprocess.check_output(['git', 'rev-parse', '--verify', 'HEAD',
                                       '--short=12']).strip()
        if hash != HASH:
            # update hash in changelog
            update_value('CHANGELOG', r'Release Name: v%s build ' % VERSION, hash)
            HASH = hash
    except subprocess.CalledProcessError: # Not a git repository
        pass


    print "Updating to:", VERSION, HASH, "on branch %s" % BRANCH

    for fname, pre in VERSION_FILES:
       update_value(fname, pre, VERSION)

    for fname, pre in HASH_FILES:
       update_value(fname, pre, HASH)

    for fname, pre in BRANCH_FILES:
        # Cut off 'v' in versioned branches
        branch = BRANCH[1:] if BRANCH[0] == 'v' else BRANCH
        update_value(fname, pre, branch)

    for fname, pre in BRANCH_FILES_V:
        update_value(fname, pre, BRANCH)

    for fname, pre in BRANCH_URLS:
        # master version of usersguide url is 'dev'
        branch = 'dev' if BRANCH in ['dev', 'master'] else BRANCH
        update_value(fname, pre, branch)

    # Update splash using inkscape
    try:
        subprocess.check_call('inkscape -e vistrails/gui/resources/images/vistrails_splash.png -w 546 dist/common/splash/splash.svg'.split())
    except (OSError, subprocess.CalledProcessError):
        print "Calling inkscape failed, make sure inkscape is installed and in your path, or generate vistrails/gui/resources/images/vistrails_splash.png manually from dist/common/splash.svg."
