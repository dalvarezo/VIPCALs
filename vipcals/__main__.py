import argparse
import os
import json
from datetime import datetime

from astropy.io import fits
from astropy.coordinates import SkyCoord

from pipeline import pipeline


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
    default_dict['userno'] = None
    default_dict['paths'] = None
    default_dict['targets'] = None
    default_dict['disk'] = None
    default_dict['calib'] = 'NONE'
    default_dict['load_all'] = False
    default_dict['shifts'] = 'NONE'
    default_dict['refant'] = 'NONE'
    default_dict['output_directory'] = 'NONE'
    default_dict['flag_edge'] = 0
    default_dict['phase_ref'] = ['NONE']

    return default_dict

parser = argparse.ArgumentParser(
                    prog = 'VIPCALs',
                    description = 'Automated VLBI data calibration pipeline using AIPS')

# Arguments are read from a json file
parser.add_argument('file', type=argparse.FileType('r'))
args = parser.parse_args()
entry_list = read_args(args.file)

## Print ASCII art ##

ascii_logo = open('./ascii_logo_string.txt', 'r').read()
print(ascii_logo)

# Iterate over every entry on the input file
print('A total of ' + str(len(entry_list)) + ' calibration blocks were read.\n')
for i, entry in enumerate(entry_list):
    print('Checking inputs of calibration block ' + str(i+1) + '.\n')
    # Create default input dictionary
    input_dict = create_default_dict()
    # Unzip inputs
    for key in entry:
        input_dict[key] = entry[key]

    ## Input sanity check ##
    # Some inputs need to be given as a list #
    if type(input_dict['paths']) != list:
        print('Filepaths have to be given as a list in the input file.\n')
        exit()
    if type(input_dict['targets']) != list:
        print('Target names have to be given as a list in the input file.\n')
        exit()
    if type(input_dict['shifts']) != list and input_dict['shifts'] != 'NONE':
        print('Coordinate shifts have to be given as a list in the input file.\n')
        exit()
    if type(input_dict['phase_ref']) != list:
        print('Phase reference calibrators have to be given as a list in ' \
        + 'the input file.\n')
        exit()

    # Load all has to be True/False
    if type(input_dict['load_all']) != bool:
        print('load_all option has to be True/False.\n')
        exit()

    # Phase reference #
    if input_dict['phase_ref'] != ['NONE']:
        if len(input_dict['targets']) != len(input_dict['phase_ref']):
            print('\nThe number of phase reference calibrators does not match ' \
            + 'the number of targets to calibrate.\n')
            exit()
    # Phase shift #
    if input_dict['shifts'] != 'NONE':
        if len(input_dict['targets']) != len(input_dict['shifts']):
            print('\nThe number of shifted coordinates does not match the number of ' \
                + 'targets to calibrate.\n')
            exit()


        for i, coord in enumerate(input_dict['shifts']):
            ra = coord.split(',')[0]
            dec = coord.split(',')[1]
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
    all_sources = list(set(all_sources))    # Remove duplicates

    for t in input_dict['targets']:
        if t not in all_sources:
            print(t + ' was not found in any of the files provided.\n')
    if any(x not in all_sources for x in input_dict['targets']):
        exit()

    # Phase reference sources have to be in the file/s
    if input_dict['phase_ref'] != ['NONE']:
        for prs in input_dict['phase_ref']:
            if prs not in all_sources:
                print(prs + ' was not found in any of the files provided.\n')
        if any(x not in all_sources for x in input_dict['phase_ref']):
            exit()

    # Load multiple files together:
    if len(input_dict['paths']) > 1:
    # Same frequency setup
#        for i, path in enumerate(input_dict['paths'],1):
#            globals()[f"hdul_{i}"] = fits.open(path)
#            
#        for j, path in enumerate(input_dict['paths'],1):
#            if (globals()[f"hdul_1"]['FREQUENCY'].data !=\
#                globals()[f"hdul_{j}"]['FREQUENCY'].data).all() == True:
#
#                print('Frequency setups of ' +  input_dict['paths'][0].split('/')[-1] \
#                    + ' and ' + path.split('/')[-1] + ' do not coincide.' \
#                    + '\nData cannot be loaded together.')
#                exit() 

    # Same project
        for j, path in enumerate(input_dict['paths'],1):
            if (globals()[f"hdul_1"][0].header['OBSERVER'] !=\
                globals()[f"hdul_{i}"][0].header['OBSERVER']) == True:

                print('Project code of ' +  input_dict['paths'][0].split('/')[-1] \
                    + ' and ' + path.split('/')[-1] + ' does not coincide.' \
                    + '\nData cannot be loaded together.')
                exit()
                
    # Similar date (+-3 days)
        obs_dates = []
        for j, path in enumerate(input_dict['paths'],1):
            YYYY = int(globals()[f"hdul_{j}"][0].header['DATE-OBS'][:4])
            MM = int(globals()[f"hdul_{j}"][0].header['DATE-OBS'][5:7])
            DD = int(globals()[f"hdul_{j}"][0].header['DATE-OBS'][8:])

            obs_dates.append(datetime(YYYY, MM, DD).toordinal())
        if (max(obs_dates) - min(obs_dates)) > 2:
            print('\nWARNING! There are more than 2 days between observations.\n')
    
    # Reference antenna #
    for filepath in input_dict['paths']:
        if input_dict['refant'] != 'NONE':
            hdul = fits.open(filepath)
            antenna_names = []
            hdul = fits.open(filepath)
            non_ascii_antennas = list(hdul['ANTENNA'].data['ANNAME'])
            for ant in non_ascii_antennas:
                ant = ant.encode()[:2].decode()
                antenna_names.append(ant)
            if input_dict['refant'] not in antenna_names:
                print('The selected reference antenna is not available in the FITS file.'\
                    + ' Please make sure that the input is correct.')
                exit()

    # Output directory
    if input_dict['output_directory'] != 'NONE':
        if os.path.isdir(input_dict['output_directory']) == False:
            print('\nThe selected output directory does not exist.' \
                + ' The pipeline will stop now.\n')
            exit()
        if input_dict['output_directory'][-1] == '/':
            input_dict['output_directory'] = input_dict['output_directory'][:-1]


    if input_dict['output_directory'] == 'NONE':
        input_dict['output_directory'] = os.getcwd()

    # Everything is fine, start the pipeline
    pipeline(input_dict)