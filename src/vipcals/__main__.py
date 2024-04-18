#!/usr/bin/env ParselTongue
# -*- coding: utf-8 -*-

import argparse
import time
import os

import numpy as np

from AIPS import AIPS

import scripts.load_data as load

from pipeline import pipeline

parser = argparse.ArgumentParser(
                    prog = 'VIPCALs',
                    description = 'Automated VLBI data calibration pipeline using AIPS')

# Positional arguments
parser.add_argument('userno', type = int)
parser.add_argument('filepath', type = str)
parser.add_argument('target', type = str)
parser.add_argument('disk_number', type = int)

# Options
op = parser.add_argument_group('options')
op.add_argument('-la', '--load_all',  required=False, action="store_true")

## Timer ##
ti = time.time()

## Inputs ##
args = parser.parse_args()
AIPS.userno = args.userno
filepath = args.filepath
filename = args.target # By default is the target's name
target = args.target
disk_number = args.disk_number
load_all = args.load_all

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
        calibs = load.find_calibrators(full_source_list)
        sources = calibs.copy()
        sources.append(target)
        # Timer per ID
        t_id = time.time() 
        if multifreq_id[2][ids] > 1e10:
            klass_1 = str(multifreq_id[2][ids])[:2] + 'G'
        else:
            klass_1 = str(multifreq_id[2][ids])[:1] + 'G'
        
        filename_id = filename + '_' + klass_1
        ## Open log ##
        if os.path.exists('./' + filename_id) == True:
            os.system('rm -rf ./' + filename_id) 
            # Let's see how to manage this, this doesn't convince me
        load.open_log(filename_id)
        
        pipeline_log = open('./' + filename_id + '/' + filename_id \
                            + '_pipeline_log.txt', 'w')
        pipeline_log.write(os.path.basename(filepath) + ' --- '\
                            + '{:.2f} MB \n'.format\
                            (os.path.getsize(filepath)/1024**2 ))
            
        ## START THE PIPELINE ##         
        pipeline(filepath, filename_id, sources, full_source_list, target,\
                    disk_number, pipeline_log, klass = klass_1, \
                    multi_id = True, selfreq = multifreq_id[2][ids]/1e6)
        
        ## Timer ##    
        tf = time.time()
        
        pipeline_log.write('\nScript run time: '\
                            + '{:.2f} s. \n'.format(tf-t_id))
        print('\nScript run time: {:.2f} s. \n'.format(tf-t_id))
        pipeline_log.close()
    exit() # STOP the pipeline. This needs to be tweaked.

    # If there are multiple IFs:   
if multifreq_if[0] == True:
    
    klass_1 = multifreq_if[5] + 'G'
    klass_2 = multifreq_if[6] + 'G'

    ## FIRST FREQUENCY ##
    ## Select sources to load ##
    full_source_list = load.get_source_list(filepath, multifreq_if[7])
    calibs = load.find_calibrators(full_source_list)
    sources = calibs.copy()
    sources.append(target)
    ## Open log ##
    filename_1 = filename + '_' + klass_1
    
    if os.path.exists('./' + filename_1) == True:
        os.system('rm -rf ./' + filename_1) 
        # Let's see how to manage this, this doesn't convince me
    
    load.open_log(filename_1)
    pipeline_log_1 = open('./' + filename_1 + '/' + filename_1 \
                        + '_pipeline_log.txt', 'w')
    pipeline_log_1.write(os.path.basename(filepath) + ' --- ' + klass_1 \
                            + ' --- {:.2f} MB \n'.format\
                            (os.path.getsize(filepath)/1024**2))
    
    ## START THE PIPELINE ##
    pipeline(filepath, filename_1, sources, full_source_list, target, \
                disk_number, pipeline_log_1, klass = klass_1,\
                bif = multifreq_if[1], eif = multifreq_if[2])
    
    tf = time.time()
    pipeline_log_1.write('\nScript run time: {:.2f} s. \n'.format(tf-ti))
    pipeline_log_1.close()
    print('\nScript run time: {:.2f} s. \n'.format(tf-ti))
    
    ## SECOND FREQUENCY ##
    ## Select sources to load ##
    full_source_list = load.get_source_list(filepath, multifreq_if[8])
    calibs = load.find_calibrators(full_source_list)
    sources = calibs.copy()
    sources.append(target)
    
    ti_2 = time.time()
    ## Open log ##
    filename_2 = filename + '_' + klass_2
    
    if os.path.exists('./' + filename_2 ) == True:
        os.system('rm -rf ./' + filename_2) 
        # Let's see how to manage this, this doesn't convince me
    
    load.open_log(filename_2)
    pipeline_log_2 = open('./' + filename_2 + '/' + filename_2 \
                        + '_pipeline_log.txt', 'w')
    pipeline_log_2.write(os.path.basename(filepath) + ' --- ' + klass_2 \
                            + ' --- {:.2f} MB \n'.format\
                            (os.path.getsize(filepath)/1024**2))
        
    ## START THE PIPELINE ##  
    pipeline(filepath, filename_2, sources, full_source_list, target, \
                disk_number, pipeline_log_2, klass = klass_2, \
                    bif = multifreq_if[3], eif = multifreq_if[4])
    
    ## Timer ##    
    tf_2 = time.time()
    pipeline_log_2.write('\nScript run time: '\
                            + '{:.2f} s. \n'.format(tf_2-ti_2))
    pipeline_log_2.close()
    print('\nScript run time: {:.2f} s. \n'.format(tf_2-ti_2))
    # End the pipeline
    exit()

# If there is only one frequency:  
if multifreq_id[0] == False and multifreq_if[0] == False:
    
    klass_1 = multifreq_if[5] + 'G'
    
    ## Select sources to load ##
    full_source_list = load.get_source_list(filepath)
    calibs = load.find_calibrators(full_source_list)
    sources = calibs.copy()
    sources.append(target)
    
    ## Open log ##
    
    if os.path.exists('./' + filename) == True:
        os.system('rm -rf ./' + filename) 
        # Let's see how to manage this, this doesn't convince me
    load.open_log(filename)
    pipeline_log = open('./' + filename + '/' + filename \
                        + '_pipeline_log.txt', 'w')
    pipeline_log.write(os.path.basename(filepath) + ' --- '\
                        + '{:.2f} MB \n'.format\
                        (os.path.getsize(filepath)/1024**2 ))
        
    ## START THE PIPELINE ##               
    pipeline(filepath, filename, sources, full_source_list, target, \
                disk_number, pipeline_log, klass = klass_1)
    
    ## Timer ##    
    tf = time.time()
    
    pipeline_log.write('\nScript run time: {:.2f} s. \n'.format(tf-ti))
    print('\nScript run time: {:.2f} s. \n'.format(tf-ti))
    pipeline_log.close()