#!/usr/bin/env python3
#
# Program to view, extract, and/or verify metadata from one or more FITS files.
#   Written by: Tom Hicks. 4/24/2018.
#   Last Modified: Update to read gzipped FITS files.
#
import getopt
import os
import fnmatch
import sys
from fits import action_dispatch

# Text file of desired metadata keys, one per line
DEFAULT_KEYS_FILE = '/fits/metadata-keys.txt'

def filter_file_tree(dir):
    "Generator to yield all files in the given file tree whose name matches the given pattern"
    fits_pat = "*.fits"                     # pattern for identifying FITS files
    gzfits_pat = "*.fits.gz"                # pattern for identifying gzipped FITS files
    for root, dirs, files in os.walk(dir):
        for file in files:
            if (fnmatch.fnmatch(file, fits_pat) or fnmatch.fnmatch(file, gzfits_pat)):
                file_path = os.path.join(root,file)
                yield file_path


def main(argv):
    "Perform actions on a FITS file or a directory of FITS files."
    options = { "action": "info", "keyfile": DEFAULT_KEYS_FILE }
    is_file = False                         # assume directory by default
    usage = "Usage: fits.py [-h|--help] [--info|--metadata|--verify] [--keyfile metadata-keyfile] images_path"

    # parse the command line arguments:
    try:
        opts, args = getopt.getopt(argv,"himvk",["help", "info", "metadata", "verify", "keyfile="])
    except getopt.GetoptError as err:
        print(err)
        print(usage)
        sys.exit(-1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit(1)
        elif opt in ("--info"):
            options["action"] = "info"
        elif opt in ("--metadata"):
            options["action"] = "metadata"
        elif opt in ("--verify"):
            options["action"] = "verify"
        elif opt in ("--keyfile"):
            options["keyfile"] = arg.strip()
        else:
            print("Error: Unrecognized command line option")
            print(usage)
            sys.exit(2)

    # check the keyfile path argument, if given
    keyfile = options.get("keyfile", DEFAULT_KEYS_FILE)
    if ((len(keyfile) < 1) or (not os.path.isfile(keyfile))):
        print("Error: --keyfile argument must specify the path to a readable key file")
        print(usage)
        sys.exit(4)

    # check the image file or directory path argument, if given
    if ((len(args) < 1) or (not args[0].strip())):
        print("Error: Missing required argument: path to image file or images directory")
        print(usage)
        sys.exit(3)

    # insure that the given path refers to a readable file or valid directory
    images_path = args[0].strip()                   # already insured non-empty above
    if (not os.path.exists(images_path)):
        print("Error: Specified images path '{}' not found or is not readable".format(images_path))
        sys.exit(5)

    if (not os.access(images_path, os.R_OK)):
        print("Error: Specified images path '{}' is not readable".format(images_path))
        sys.exit(6)

    if (os.path.isfile(images_path)):
        action_dispatch(images_path, options)
    else:
        if (os.path.isdir(images_path)):
            for fits_file in filter_file_tree(images_path):
                action_dispatch(fits_file, options)
        else:
            print("Error: Specified images path '{}' is not a file or directory".format(images_path))
            sys.exit(7)


if __name__ == '__main__':
    main(sys.argv[1:])
