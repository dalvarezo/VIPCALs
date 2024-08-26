#!/usr/bin/env ParselTongue
# -*- coding: utf-8 -*-

import argparse
import time
import os

import numpy as np

from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord

from AIPS import AIPS

import scripts.load_data as load

from pipeline import pipeline

parser = argparse.ArgumentParser(
                    prog = 'VIPCALs',
                    description = 'Automated VLBI data calibration pipeline using AIPS')

# Positional arguments
parser.add_argument('-u', '--userno', type = int)
parser.add_argument('-d', '--disk_number', type = int)
parser.add_argument('-p', '--filepath', type = str)
parser.add_argument('-t', '--target', nargs = '+')


# Optional arguments
opargs = parser.add_argument_group('optional arguments')
parser.add_argument('-c', '--calibrator', required = False, type = str, default = 'NONE')
parser.add_argument('-r', '--refant', required = False, type = str, default = 'NONE')
parser.add_argument('-s', '--shift', required = False, type = str, nargs = '+',\
                     default = 'NONE')
parser.add_argument('-o', '--output_directory', required = False, type = str, \
                    default = 'NONE')

# Options
options = parser.add_argument_group('options')
options.add_argument('-la', '--load_all',  required = False, action = "store_true")

## Timer ##
ti = time.time()

## Inputs ##
args = parser.parse_args()
AIPS.userno = args.userno
filepath = args.filepath
filename_list = args.target # By default is the target's name
target_list = args.target
disk_number = args.disk_number
inp_cal = args.calibrator
load_all = args.load_all
shifts = args.shift
def_refant = args.refant
output_directory = args.output_directory

## Print ASCII art ##

ascii_logo = open('./ascii_logo_string.txt', 'r').read()
print(ascii_logo)

## Input sanity check ##
# Phase shift #
if shifts != 'NONE':
    if len(target_list) != len(shifts):
        print('\nThe number of shifted coordinates does not match the number of ' \
              + 'targets to calibrate.\n')
        exit()


    for i, coord in enumerate(shifts):
        ra = coord.split(',')[0]
        dec = coord.split(',')[1]
        try:
            shifts[i] =  SkyCoord(ra, dec, unit = 'deg')
        except: 
            print('\nThere was an error while reading the phase-shift coordinates.' \
                  + ' Please make sure that the input is correct.\n')
            exit()

# Reference antenna
if def_refant != 'NONE':
    hdul = fits.open(filepath)
    antenna_names = []
    hdul = fits.open(filepath)
    non_ascii_antennas = list(Table(hdul['ANTENNA'].data)['ANNAME'])
    for ant in non_ascii_antennas:
        ant = ant.encode()[:2].decode()
        antenna_names.append(ant)
    if def_refant not in antenna_names:
        print('The selected reference antenna is not available in the FITS file.' \
              + ' Please make sure that the input is correct.')
        exit()


# Output directory
if output_directory != 'NONE':
    if os.path.isdir(output_directory) == False:
        print('\nThe selected output directory does not exist.' \
              + ' The pipeline will stop now.\n')
        exit()
    if output_directory[-1] == '/':
        output_directory = output_directory[:-1]


if output_directory == 'NONE':
    output_directory = os.getcwd()


## Check for multiband datasets ##
# In IDs    
multifreq_id = load.is_it_multifreq_id(filepath)
# In IFs
multifreq_if = load.is_it_multifreq_if(filepath)

# If there are multiple IDs:
if multifreq_id[0] == True:
    for ids in range(multifreq_id[1]):
        ## Select sources to load ##
        full_source_list = load.get_source_list(filepath, multifreq_id[2][ids])
        if load_all == False:
            calibs = load.find_calibrators(full_source_list)
            sources = calibs.copy()
            sources += target_list
        if load_all == True:
            sources = [x.name for x in full_source_list]

        if multifreq_id[2][ids] > 1e10:
            klass_1 = str(multifreq_id[2][ids])[:2] + 'G'
        else:
            klass_1 = str(multifreq_id[2][ids])[:1] + 'G'

        # Define AIPS name
        hdul = fits.open(filepath)
        aips_name = hdul[0].header['OBSERVER'] + '_' + klass_1

        ## Check if the AIPS catalogue name is too long, and rename ##
        # 12 is the maximum length for a file name in AIPS
        aips_name_short = aips_name
        if len(aips_name) > 12:
            name = aips_name.split('_')[0]
            suffix = aips_name.split('_')[1]
            size_name = 12 - (len(suffix) + 1)
            aips_name_short = name[:size_name] + '_' + suffix

        # Check if project directory already exists, if not, create one
        project_dir = output_directory + '/' + hdul[0].header['OBSERVER']
        if os.path.exists(project_dir) == False:
            os.system('mkdir ' + project_dir)

        # Create subdirectories for the targets and DELETE EXISTING ONES
        # Also, create the pipeline log file of each target
        filename_list = target_list.copy()
        log_list = target_list.copy()
        path_list = target_list.copy()
        for i, name in enumerate(filename_list):
            filename_list[i] = name + '_' + klass_1
            path_list[i] = project_dir + '/' + filename_list[i]
            if os.path.exists(project_dir + '/' + filename_list[i]) == True:
                os.system('rm -rf ' + project_dir + '/' + filename_list[i])
            os.system('mkdir ' + project_dir + '/' + filename_list[i])

            log_list[i] = open(project_dir + '/' + filename_list[i] + '/' + name \
                        + '_pipeline_log.txt', 'w+')
            log_list[i].write(ascii_logo + '\n')
            log_list[i].write(os.path.basename(filepath) + ' --- '\
                                + '{:.2f} MB \n'.format\
                                (os.path.getsize(filepath)/1024**2 ))

        ## START THE PIPELINE ##         
        pipeline(filepath, aips_name_short, sources, full_source_list, target_list,\
                    filename_list, log_list, path_list, \
                    disk_number, klass = klass_1, \
                    multi_id = True, selfreq = multifreq_id[2][ids]/1e6,\
                    default_refant = def_refant, input_calibrator = inp_cal, \
                    load_all = load_all, shift_coords = shifts)
        
    exit() # STOP the pipeline. This needs to be tweaked.

# If there are multiple IFs:   
if multifreq_if[0] == True:
    
    klass_1 = multifreq_if[5] + 'G'
    klass_2 = multifreq_if[6] + 'G'

    ## FIRST FREQUENCY ##
    ## Select sources to load ##
    full_source_list = load.get_source_list(filepath, multifreq_if[7])
    if load_all == False:
        calibs = load.find_calibrators(full_source_list)
        sources = calibs.copy()
        sources += target_list
    if load_all == True:
        sources = [x.name for x in full_source_list]

    # Define AIPS name
    hdul = fits.open(filepath)
    aips_name = hdul[0].header['OBSERVER'] + '_' + klass_1

    ## Check if the AIPS catalogue name is too long, and rename ##
    aips_name_short = aips_name
    if len(aips_name) > 12:
        name = aips_name.split('_')[0]
        suffix = aips_name.split('_')[1]
        size_name = 12 - (len(suffix) + 1)
        aips_name_short = name[:size_name] + '_' + suffix

    # Check if project directory already exists, if not, create one
    project_dir = output_directory + '/' + hdul[0].header['OBSERVER']
    if os.path.exists(project_dir) == False:
        os.system('mkdir ' + project_dir)

    # Create subdirectories for the targets and DELETE EXISTING ONES
    # Also, create the pipeline log file of each target
    filename_list = target_list.copy()
    log_list = target_list.copy()
    path_list = target_list.copy()
    for i, name in enumerate(filename_list):
        filename_list[i] = name + '_' + klass_1
        path_list[i] = project_dir + '/' + filename_list[i]
        if os.path.exists(project_dir + '/' + filename_list[i]) == True:
            os.system('rm -rf ' + project_dir + '/' + filename_list[i])
        os.system('mkdir ' + project_dir + '/' + filename_list[i])

        log_list[i] = open(project_dir + '/' + filename_list[i] + '/' + name \
                    + '_pipeline_log.txt', 'w+')
        log_list[i].write(ascii_logo + '\n')
        log_list[i].write(os.path.basename(filepath) + ' --- '\
                            + '{:.2f} MB \n'.format\
                            (os.path.getsize(filepath)/1024**2 ))
    
    ## START THE PIPELINE ##
    pipeline(filepath, aips_name_short, sources, full_source_list, target_list, \
             filename_list, log_list, path_list, \
             disk_number, klass = klass_1,\
             bif = multifreq_if[1], eif = multifreq_if[2], \
             default_refant = def_refant, input_calibrator = inp_cal, \
             load_all = load_all, shift_coords = shifts)
    

    ## SECOND FREQUENCY ##
    ## Select sources to load ##
    full_source_list = load.get_source_list(filepath, multifreq_if[8])
    if load_all == False:
        calibs = load.find_calibrators(full_source_list)
        sources = calibs.copy()
        sources += target_list
    if load_all == True:
        sources = [x.name for x in full_source_list]
    
    # Define AIPS name
    hdul = fits.open(filepath)
    aips_name = hdul[0].header['OBSERVER'] + '_' + klass_2
    
    ## Check if the AIPS catalogue name is too long, and rename ##
    aips_name_short = aips_name
    if len(aips_name) > 12:
        name = aips_name.split('_')[0]
        suffix = aips_name.split('_')[1]
        size_name = 12 - (len(suffix) + 1)
        aips_name_short = name[:size_name] + '_' + suffix

    # Check if project directory already exists, if not, create one
    project_dir = output_directory + '/' + hdul[0].header['OBSERVER']
    if os.path.exists(project_dir) == False:
        os.system('mkdir ' + project_dir)

    # Create subdirectories for the targets and DELETE EXISTING ONES
    # Also, create the pipeline log file of each target
    filename_list = target_list.copy()
    log_list = target_list.copy()
    path_list = target_list.copy()
    for i, name in enumerate(filename_list):
        filename_list[i] = name + '_' + klass_2
        path_list[i] = project_dir + '/' + filename_list[i]
        if os.path.exists(project_dir + '/' + filename_list[i]) == True:
            os.system('rm -rf ' + project_dir + '/' + filename_list[i])
        os.system('mkdir ' + project_dir + '/' + filename_list[i])

        log_list[i] = open(project_dir + '/' + filename_list[i] + '/' + name \
                    + '_pipeline_log.txt', 'w+')
        log_list[i].write(ascii_logo + '\n')
        log_list[i].write(os.path.basename(filepath) + ' --- '\
                            + '{:.2f} MB \n'.format\
                            (os.path.getsize(filepath)/1024**2 ))
        
    ## START THE PIPELINE ##  
    pipeline(filepath, aips_name_short, sources, full_source_list, target_list, \
             filename_list, log_list, path_list, \
             disk_number, klass = klass_2, \
             bif = multifreq_if[3], eif = multifreq_if[4], default_refant = def_refant, \
             input_calibrator = inp_cal, load_all = load_all, shift_coords = shifts)

    # End the pipeline
    exit()

# If there is only one frequency:  
if multifreq_id[0] == False and multifreq_if[0] == False:
    
    klass_1 = multifreq_if[5] + 'G'
    
    ## Select sources to load ##
    full_source_list = load.get_source_list(filepath)
    if load_all == False:
        calibs = load.find_calibrators(full_source_list)
        sources = calibs.copy()
        sources += target_list
    if load_all == True:
        sources = [x.name for x in full_source_list]

    # Define AIPS name
    hdul = fits.open(filepath)
    aips_name = hdul[0].header['OBSERVER'] 
    
    ## Check if the AIPS catalogue name is too long, and rename ##
    aips_name_short = aips_name
    if len(aips_name) > 12:
        name = aips_name.split('_')[0]
        suffix = aips_name.split('_')[1]
        size_name = 12 - (len(suffix) + 1)
        aips_name_short = name[:size_name] + '_' + suffix

    # Check if project directory already exists, if not, create one
    project_dir = output_directory + '/' + hdul[0].header['OBSERVER']
    if os.path.exists(project_dir) == False:
        os.system('mkdir ' + project_dir)

    # Create subdirectories for the targets and DELETE EXISTING ONES
    # Also, create the pipeline log file of each target
    filename_list = target_list.copy()
    log_list = target_list.copy()
    path_list = target_list.copy()
    for i, name in enumerate(filename_list):
        filename_list[i] = name + '_' + klass_1
        path_list[i] = project_dir + '/' + filename_list[i]
        
        if os.path.exists(project_dir + '/' + filename_list[i]) == True:
            os.system('rm -rf ' + project_dir + '/' + filename_list[i])
        os.system('mkdir ' + project_dir + '/' + filename_list[i])

        log_list[i] = open(project_dir + '/' + filename_list[i] + '/' + name \
                    + '_pipeline_log.txt', 'w+')
        log_list[i].write(ascii_logo + '\n')
        log_list[i].write(os.path.basename(filepath) + ' --- '\
                            + '{:.2f} MB \n'.format\
                            (os.path.getsize(filepath)/1024**2 ))
        
    ## START THE PIPELINE ##               
    pipeline(filepath, aips_name, sources, full_source_list, target_list, \
             filename_list, log_list, path_list, \
             disk_number, klass = klass_1, default_refant = def_refant, \
             input_calibrator = inp_cal, load_all = load_all, shift_coords = shifts)