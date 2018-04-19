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
DESIRED_KEYS_FILE = 'metadata-keys.txt'

def filter_file_tree(dir, pattern):
    "Generator to yield all files in the given file tree whose name matches the given pattern"
    for root, dirs, files in os.walk(dir):
        for file in files:
            if (fnmatch.fnmatch(file, pattern)):
                file_path = os.path.join(root,file)
                yield file_path

def get_desired_metadata_keys():
    "Return a list of metadata keys to be extracted"
    with open(DESIRED_KEYS_FILE, 'r') as mdkeys_file:
        return mdkeys_file.read().splitlines()

def handle_ctype_mapping(key, file_metadata, metadata):
    if (key == 'CRVAL1'):
        if 'RA' in hdu.header['CTYPE1']:
            metadata.append( (key, str(file_metadata.get('right_ascension', ''))) )
        elif 'DEC' in hdu.header['CTYPE1']:
            metadata.append( (key, str(file_metadata.get('declination', ''))) )
        else:
            metadata.append( (key, '') )
    elif (key == 'CRVAL2'):
        if 'RA' in hdu.header['CTYPE2']:
            metadata.append( (key, str(file_metadata.get('right_ascension', ''))) )
        elif 'DEC' in hdu.header['CTYPE2']:
            metadata.append( (key, str(file_metadata.get('declination', ''))) )
        else:
            metadata.append( (key, '') )

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
                metadata.append( (standard_key, str(file_metadata.get(standard_key, ''))) )
            elif (key == 'CRVAL1') or (key == 'CRVAL2'):
                handle_ctype_mapping(key, file_metadata, metadata)
            else:                                           # just lookup the given key
                metadata.append( (key, str(file_metadata.get(key, ''))) )
        except KeyError:
            metadata.append( (key, '') )
    return metadata

def fits_extract(file_path):
    "Extract a dictionary of metadata from the given FITS file"
    desired_keys = get_desired_metadata_keys()
    with fits.open(file_path) as hdu:
        metadata = extract_metadata(file_path, hdu, desired_keys)
        print("METADATA= " + str(metadata))    ##### REMOVE LATER

def fits_info(file_path):
    "Print the Header Data Unit information for the given FITS file"
    with fits.open(file_path) as hdus:
        print(hdus.info())
        for hdu in hdus:
            hdu.verify('silentfix+ignore')
            hdr = hdu.header
            for key in hdr.keys():
                val = str(hdr[key])
                if (key and val):                       # ignore blank keys or values
                    print(key + ': ' + val)
        print()

def fits_verify(file_path, problems_file):
    """Verify that the data in the given FITS file conforms to the FITS standard.
       Writes any verification warnings to the specified problem log file.
    """
    with fits.open(file_path) as hdu:
        with warnings.catch_warnings(record=True) as warns:
            hdu.verify('fix+warn')
            if (warns and len(warns) > 0):
                with open(problems_file, 'a') as log:
                    log.write("FILE: " + file_path)
                    for warn in warns:
                        log.write(str(warn.message)+'\n')

def main(argv):
    """Validate the meta-data for all FITS files in the given file tree.
    """
    action = "info"
    fits_pat = "*.fits"
    problems_file = "problems.txt"
    usage = "Usage: fits.py [-h|--help] [--info|--extract|--verify] images_directory"

    # parse the command line arguments:
    try:
        opts, args = getopt.getopt(argv,"hiv",["help", "info", "extract", "verify"])
    except getopt.GetoptError:
        print(usage)
        sys.exit(-1)
    # grab the image directory path argument, if given
    if (len(args) < 1):
        print("Error: Missing required argument: images directory")
        print(usage)
        sys.exit(1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(usage)
            sys.exit(2)
        elif opt in ("--info"):
            action = "info"
        elif opt in ("--extract"):
            action = "extract"
        elif opt in ("--verify"):
            action = "verify"
        else:
            print("Error: Unrecognized command line option")
            print(usage)
            sys.exit(3)

    # grab and check the image directory path argument, which must be here
    images_dir = args[0].strip()
    if (not images_dir or (not os.path.isdir(images_dir))):
        print("Error: Specified images directory '{}' not found or is not a directory".format(images_dir))
        print(usage)
        sys.exit(1)

    for file in filter_file_tree(images_dir, fits_pat):
        if (action == "info"):
            fits_info(file)
        elif (action == "extract"):
            fits_extract(file)
        elif (action == "verify"):
            fits_verify(file, problems_file)

if __name__ == '__main__':
    main(sys.argv[1:])
