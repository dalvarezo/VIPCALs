#!/usr/bin/env ParselTongue
# -*- coding: utf-8 -*-

import argparse
import time
import os

import numpy as np

from astropy.io import fits
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

## Input sanity check ##

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
        if len(target_list) == 1:
            aips_name = target_list[0] + '_' + klass_1
        else:
            hdul = fits.open(filepath)
            aips_name = hdul[0].header['OBSERVER'] + '_' + klass_1

        ## START THE PIPELINE ##         
        pipeline(filepath, aips_name, sources, full_source_list, target_list,\
                    disk_number, klass = klass_1, \
                    multi_id = True, selfreq = multifreq_id[2][ids]/1e6,\
                    default_refant = def_refant, input_calibrator = inp_cal, \
                    load_all = load_all, shift_coords = shifts)
        
         # Copy logs
        if len(target_list)>1:
            load.copy_log(target_list, klass_1)
        
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
    if len(target_list) == 1:
        aips_name = target_list[0] + '_' + klass_1
    else:
        hdul = fits.open(filepath)
        aips_name = hdul[0].header['OBSERVER'] + '_' + klass_1
    
    ## START THE PIPELINE ##
    pipeline(filepath, aips_name, sources, full_source_list, target_list, \
             disk_number, klass = klass_1,\
             bif = multifreq_if[1], eif = multifreq_if[2], \
             default_refant = def_refant, input_calibrator = inp_cal, \
             load_all = load_all, shift_coords = shifts)
    
    # Copy logs
    if len(target_list)>1:
        load.copy_log(target_list, klass_1)

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
    if len(target_list) == 1:
        aips_name = target_list[0] + '_' + klass_2
    else:
        hdul = fits.open(filepath)
        aips_name = hdul[0].header['OBSERVER'] + '_' + klass_2
        
    ## START THE PIPELINE ##  
    pipeline(filepath, aips_name, sources, full_source_list, target_list, \
             disk_number, klass = klass_2, \
             bif = multifreq_if[3], eif = multifreq_if[4], default_refant = def_refant, \
             input_calibrator = inp_cal, load_all = load_all, shift_coords = shifts)

    # Copy logs
    if len(target_list)>1:
        load.copy_log(target_list, klass_2)

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
    if len(target_list) == 1:
        aips_name = target_list[0] 
    else:
        hdul = fits.open(filepath)
        aips_name = hdul[0].header['OBSERVER'] 
        
    ## START THE PIPELINE ##               
    pipeline(filepath, aips_name, sources, full_source_list, target_list, \
             disk_number, klass = klass_1, default_refant = def_refant, \
             input_calibrator = inp_cal, load_all = load_all, shift_coords = shifts)
    
    # Copy logs
    if len(target_list)>1:
        load.copy_log(target_list, klass_1)