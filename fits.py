#!/usr/bin/env python3

#
# Program to view, extract, and/or verify metadata from one or more FITS files.
#   Written by: Tom Hicks. 4/24/2018.
#   Last Modified: Dont change metadata value types. Filter missing values.
#

import getopt
import os
import fnmatch
import sys
import warnings
from astropy.io import fits

# Dictionary of alternates for more standard metadata keys
ALTERNATE_KEYS_MAP = {
'spatial_axis_1_number_bins': 'NAXIS1',
'spatial_axis_2_number_bins': 'NAXIS2',
'start_time': 'DATE-OBS',
'facility_name': 'INSTRUME',
'instrument_name': 'TELESCOP',
'obs_creator_name': 'OBSERVER',
'obs_title': 'OBJECT'
}
ALTERNATE_KEYS = set(ALTERNATE_KEYS_MAP.keys())
DEFAULT_KEYS_FILE = '/fits/metadata-keys.txt'

def action_dispatch(fits_file, options):
    "Dispatch the given FITS file to the appropriate action"
    action = options.get("action", "info")
    if (action == "info"):
        fits_info(fits_file, options)
    elif (action == "metadata"):
        metadata = fits_metadata(fits_file, options)
        print(str(metadata))
        # print("METADATA(" + str(len(metadata)) + ")=" + str(metadata))
    elif (action == "verify"):
        fits_verify(fits_file, options)
    else:
        print("Error: Unrecognized action: '{}'".format(action))
        sys.exit()

def extract_metadata(file_path, hdu, desired_keys):
    """Extract the metadata from the HeaderDataUnit of the given file for the keys
       in the given list of sought keys. Return a list of metadata key/value tuples."""
    fnorp = 'file name or path'
    file_metadata = hdu[0].header
    metadata = []                                   # return list of metadata key/value tuples
    for key in desired_keys:
        try:
            if (key == fnorp):                              # special case: include file path
                metadata.append( (fnorp, str(file_path)) )
            elif (key in ALTERNATE_KEYS):                   # is this an alternate key?
                standard_key = ALTERNATE_KEYS_MAP[key]      # get more standard key
                metadata.append( (key, file_metadata.get(standard_key)) )
            elif ((key == 'CRVAL1') or (key == 'CRVAL2')):
                handle_ctype_mapping(key, file_metadata, metadata)
            else:                                           # just lookup the given key
                metadata.append( (key, file_metadata.get(key)) )
        except KeyError:
            metadata.append( (key, '') )
    return metadata

def filter_file_tree(dir, pattern):
    "Generator to yield all files in the given file tree whose name matches the given pattern"
    for root, dirs, files in os.walk(dir):
        for file in files:
            if (fnmatch.fnmatch(file, pattern)):
                file_path = os.path.join(root,file)
                yield file_path

def fits_metadata(file_path, options):
    "Return a list of key/value metadata tuples (strings) extracted from the given FITS file"
    desired_keys = get_metadata_keys(options)
    with fits.open(file_path) as hdu:
        metadata = extract_metadata(file_path, hdu, desired_keys)
    # filter out any metadata key/value pairs without values
    return [md for md in metadata if md[1]]

def fits_info(file_path, options):
    "Print the Header Data Unit information for the given FITS file"
    with fits.open(file_path) as hdus:
        print(hdus.info())
        for hdu in hdus:
            hdu.verify('silentfix+ignore')
            hdr = hdu.header
            for key in hdr.keys():
                val = str(hdr[key])
                if (key and val):                   # ignore blank keys or values
                    print(key + ': ' + val)
        print()

def fits_verify(file_path, options):
    """Verify that the data in the given FITS file conforms to the FITS standard.
       Writes any verification warnings to the specified problem log file.
    """
    problems_file = "problems.txt"
    with fits.open(file_path) as hdu:
        with warnings.catch_warnings(record=True) as warns:
            hdu.verify('fix+warn')
            if (warns and len(warns) > 0):
                print("Filename: " + file_path)
                for warn in warns:
                    print(str(warn.message))

def get_metadata_keys(options):
    "Return a list of metadata keys to be extracted"
    keyfile = options.get("keyfile", DEFAULT_KEYS_FILE)
    with open(keyfile, 'r') as mdkeys_file:
        return mdkeys_file.read().splitlines()

def handle_ctype_mapping(key, file_metadata, metadata):
    """If key is a special value which provides the meaning of other fields, then
       add the key and its value and then write the referenced value with a another key.
       For CRVALs and how they relate to CRTYPEs see https://fits.gsfc.nasa.gov/fits_standard.html
    """
    if (key == 'CRVAL1'):
        metadata.append( ('CRVAL1', file_metadata.get('CRVAL1')) )
        if 'RA' in file_metadata['CTYPE1']:
            metadata.append( ('right_ascension', file_metadata.get('CRVAL1')) )
        elif 'DEC' in file_metadata['CTYPE1']:
            metadata.append( ('declination', file_metadata.get('CRVAL1')) )
        else:
            metadata.append( (key, '') )
    elif (key == 'CRVAL2'):
        metadata.append( ('CRVAL2', file_metadata.get('CRVAL2')) )
        if 'RA' in file_metadata['CTYPE2']:
            metadata.append( ('right_ascension', file_metadata.get('CRVAL2')) )
        elif 'DEC' in file_metadata['CTYPE2']:
            metadata.append( ('declination', file_metadata.get('CRVAL2')) )
        else:
            metadata.append( (key, '') )


def main(argv):
    "Perform actions on a FITS file or a directory of FITS files."
    options = { "action": "info", "keyfile": DEFAULT_KEYS_FILE }
    is_file = False                             # assume directory by default
    fits_pat = "*.fits"                         # pattern for identifying FITS files
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
        if (not os.path.isdir(images_path)):
            print("Error: Specified images path '{}' is not a file or a directory".format(images_path))
            sys.exit(7)
        else:
            for fits_file in filter_file_tree(images_path, fits_pat):
                action_dispatch(fits_file, options)


if __name__ == '__main__':
    main(sys.argv[1:])
