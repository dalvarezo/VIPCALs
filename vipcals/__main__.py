import argparse
import os
import json
import string
from datetime import datetime

from astropy.io import fits
from astropy.coordinates import SkyCoord

from pipeline import pipeline

import functools
print = functools.partial(print, flush=True)


def read_args(file):
    """Read arguments from a json file and return them as a list of dictionaries.

    :param file: _description_
    :type file: _type_
    :return: _description_
    :rtype: _type_
    """
	# List to store dictionaries
    dict_list = []
    current_block = []
    
    for line in file:
		    # Strip leading/trailing whitespace
            stripped_line = line.strip()
		    # If the line is not empty, add it to the current block
            if stripped_line:
                current_block.append(stripped_line)
            else:
		        # If we encounter an empty line, process the current block
                if current_block:
                # Join lines and parse as JSON
                    block_str = ' '.join(current_block)
                    try:
                        dict_obj = json.loads(block_str)
                        dict_list.append(dict_obj)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing block: {block_str}\n{e}")
                    # Clear current block for next dictionary
                    current_block = []	

	# Handle the last block if the file doesn't end with a blank line
    if current_block:
        block_str = ' '.join(current_block)
        try:
            dict_obj = json.loads(block_str)
            dict_list.append(dict_obj)
        except json.JSONDecodeError as e:
            print(f"Error parsing block: {block_str}\n{e}")

    return dict_list

def create_default_dict():
    """Create an input dictionary with default inputs.

    :return: dictionary with default inputs
    :rtype: dict
    """
    default_dict = {}
    # Basic inputs
    default_dict['userno'] = None
    default_dict['disk'] = None
    default_dict['paths'] = None
    default_dict['targets'] = None
    default_dict['output_directory'] = None
    # Calibration options
    default_dict['calib'] = None
    default_dict['calib_all'] =  False
    default_dict['phase_ref'] = None
    # Loading options
    default_dict['load_all'] = False
    default_dict['freq_sel'] = None
    default_dict['subarray'] = False
    default_dict['shifts'] = None
    # Reference antenna options
    default_dict['refant'] = None
    default_dict['refant_list'] = None
    default_dict['search_central'] = True
    default_dict['max_scan_refant_search'] = 10
    # Fringe options
    default_dict['solint'] = None
    default_dict['min_solint'] = 1
    default_dict['max_solint'] = 10
    # Export options
    default_dict['channel_out'] = 'SINGLE'
    default_dict['flag_edge'] = 0
    # Plotting options
    default_dict['interactive'] = True

    return default_dict

parser = argparse.ArgumentParser(
                    prog = 'VIPCALs',
                    description = 'Automated VLBI data calibration pipeline using AIPS')

# Arguments are read from a json file
parser.add_argument('file', type=argparse.FileType('r'))
args = parser.parse_args()
entry_list = read_args(args.file)

## Print ASCII art ##

ascii_logo = open('../GUI/ascii_logo_string.txt', 'r').read()
print(ascii_logo)

# Iterate over every entry on the input file
print('A total of ' + str(len(entry_list)) + ' calibration blocks were read.\n')
for i, entry in enumerate(entry_list):
    print('Checking inputs of calibration block ' + str(i+1) + '.\n')
    # Create default input dictionary
    input_dict = create_default_dict()
    # Unzip inputs
    for key in entry:
        if entry[key] != "":
            input_dict[key] = entry[key]

    ## Input sanity check ##
    # Some inputs need to be integers #
    try:
        input_dict['userno'] = int(input_dict['userno'])
    except ValueError:
        print('User number has to be a number.\n')
        exit()
    try:
        input_dict['disk'] = int(input_dict['disk'])
    except ValueError:
        print('Disk number has to be a number.\n')
        exit()

    # Some inputs need to be given as a list #
    if type(input_dict['paths']) != list:
        print('Filepaths have to be given as a list in the input file.\n')
        exit()
    if type(input_dict['targets']) != list:
        print('Target names have to be given as a list in the input file.\n')
        exit()
    if type(input_dict['shifts']) != list and input_dict['shifts'] != None:
        print('Coordinate shifts have to be given as a list in the input file.\n')
        exit()
    if type(input_dict['phase_ref']) != list:
        print('Phase reference calibrators have to be given as a list in ' \
        + 'the input file.\n')
        exit()

    print(input_dict['paths'])
    print('\n')

    # Load all has to be True/False
    if type(input_dict['load_all']) != bool:
        print('load_all option has to be True/False.\n')
        exit()

    # subarrays has to be True/False
    if type(input_dict['subarrays']) != bool:
        print('subarrays option has to be True/False.\n')
        exit()

    # Phase reference #
    if input_dict['phase_ref'] != None:
        if len(input_dict['targets']) != len(input_dict['phase_ref']):
            print('\nThe number of phase reference calibrators does not match ' \
            + 'the number of targets to calibrate.\n')
            exit()
    # Phase shift #
    if input_dict['shifts'] != None:
        if len(input_dict['targets']) != len(input_dict['shifts']):
            print('\nThe number of shifted coordinates does not match the number of ' \
                + 'targets to calibrate.\n')
            exit()


        for i, coord in enumerate(input_dict['shifts']):
            ra = coord[0]
            dec = coord[1]
            try:
                input_dict['shifts'][i] =  SkyCoord(ra, dec, unit = 'deg')
            except: 
                print('\nThere was an error while reading the phase-shift coordinates.' \
                    + ' Please make sure that the input is correct.\n')
                exit()

    # Science targets have to be in the file/s
    all_sources = []
    for i, path in enumerate(input_dict['paths'],1):
            globals()[f"hdul_{i}"] = fits.open(path)
            all_sources.extend(list(globals()[f"hdul_{i}"]['SOURCE'].data['SOURCE']))
            globals()[f"hdul_{i}"].close()
    all_sources = list(set(all_sources))    # Remove duplicates
    # Clean the list from non ASCII characters
    try:
        all_sources_clean = [''.join(c for c in item.decode('ascii', 'ignore') if c in \
                                    string.printable) for item in all_sources]
    except AttributeError:
        all_sources_clean = all_sources

    for t in input_dict['targets']:
        if t not in all_sources_clean:
            print(t + ' was not found in any of the files provided.\n')
    if any(x not in all_sources_clean for x in input_dict['targets']):
        exit()

    # Phase reference sources have to be in the file/s
    if input_dict['phase_ref'] != None:
        for prs in input_dict['phase_ref']:
            if prs == 'NONE':
                continue
            if prs not in all_sources:
                print(prs + ' was not found in any of the files provided.\n')
        if any(x not in all_sources for x in input_dict['phase_ref'] if x != 'NONE'):
            exit()

    # Load multiple files together:
    if len(input_dict['paths']) > 1:
                
    # Similar date (+-3 days)
        obs_dates = []
        for j, path in enumerate(input_dict['paths'],1):
            for fmt in ("%d/%m/%y", "%Y-%m-%d"):
                try:
                    #print(globals()[f"hdul_{j}"][0].header['DATE-OBS'])
                    dt = datetime.strptime(globals()[f"hdul_{j}"][0].header['DATE-OBS'], fmt)
                    YYYY, MM, DD = dt.year, dt.month, dt.day
                    obs_dates.append(datetime(YYYY, MM, DD).toordinal())
                except ValueError:
                    continue
                
        if (max(obs_dates) - min(obs_dates)) > 2:
            print('\nWARNING! There are more than 2 days between observations.\n')

        if len(obs_dates) == 0:
            raise ValueError("Incorrect date format")
    
    # Reference antenna #
    for filepath in input_dict['paths']:
        if input_dict['refant'] != None:
            antenna_names = []
            hdul = fits.open(filepath)
            non_ascii_antennas = list(hdul['ANTENNA'].data['ANNAME'])
            hdul.close()
            for ant in non_ascii_antennas:
                ant = ant.encode()[:2].decode()
                antenna_names.append(ant)
            if input_dict['refant'] not in antenna_names:
                print('The selected reference antenna is not available in the FITS file.'\
                    + ' Please make sure that the input is correct.')
                exit()

    # Output directory
    if input_dict['output_directory'] != None:
        if os.path.isdir(input_dict['output_directory']) == False:
            print('\nThe selected output directory does not exist.' \
                + ' The pipeline will stop now.\n')
            exit()
        if input_dict['output_directory'][-1] == '/':
            input_dict['output_directory'] = input_dict['output_directory'][:-1]


    if input_dict['output_directory'] == None:
        input_dict['output_directory'] = os.getcwd()

    # Everything is fine, start the pipeline
    pipeline(input_dict)