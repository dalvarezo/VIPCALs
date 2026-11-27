import os
import time 
import json
import pickle
import shutil
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

from AIPS import AIPS

from astropy.coordinates import SkyCoord
from astropy.io import fits

from vipcals.scripts import load_data as load
from vipcals.scripts import display as disp
from vipcals.scripts import load_tables as tabl
from vipcals.scripts import ty_smooth as tysm
from vipcals.scripts import refant_choose as rant
from vipcals.scripts import ionos_corr as iono
from vipcals.scripts import eop_corr as eopc
from vipcals.scripts import accor as accr
from vipcals.scripts import amp_cal as ampc
from vipcals.scripts import pang_corr as pang
from vipcals.scripts import calib_choose as cali
from vipcals.scripts import instr_calib as inst
from vipcals.scripts import plotter as plot
from vipcals.scripts import bandpass as bpas
from vipcals.scripts import helper as help
from vipcals.scripts import fringe_fit as frng
from vipcals.scripts import optimize_solint as opti
from vipcals.scripts import export_data as expo
from vipcals.scripts import phase_shift as shft


from AIPSData import AIPSUVData, AIPSCat
import Wizardry.AIPSData as wizard

import functools
print = functools.partial(print, flush=True)

tmp_dir = os.path.expanduser("~/.vipcals/tmp")

# Check if /home/vipcals exists
if os.path.isdir("/home/vipcals"):
    tmp_dir = "/home/vipcals/.vipcals/tmp"

def calibrate(filepath_list, filename_list, outpath_list, log_list, target_list, 
              sources, load_all, full_source_list, disk_number, aips_name, klass, 
              multi_id, selfreq, if_idx, default_refant, default_refant_list, 
              search_central, max_scan_refant_search, time_aver, freq_aver, 
              fringefit_snr, default_solint, min_solint, 
              max_solint, phase_ref, input_calibrator, shift_coords, 
              load_antab, load_flags, channel_out, flag_edge, interactive, stats_df):

    """Main workflow of the pipeline 

    :param filepath_list: list of paths to the original uvfits/idifits files
    :type filepath_list: list of str
    :param filename_list: list containing the names of the subdirectories of each target
    :type filename_list: list of str
    :param outpath_list: list containing the output file paths for each target
    :type outpath_list: list of str
    :param log_list: list of log files
    :type log_list: list of file
    :param target_list: science target names
    :type target_list: list of str
    :param sources: all sources to be loaded
    :type sources: list of str
    :param load_all: load all sources on the dataset
    :type load_all: bool
    :param full_source_list: list containing all sources in the dataset
    :type full_source_list: list of :class:`~vipcals.scripts.helper.Source` objects
    :param disk_number: disk number within AIPS
    :type disk_number: int
    :param aips_name: name for the catalogue entry in AIPS
    :type aips_name: str
    :param klass: class name within AIPS
    :type klass: str
    :param multi_id: whether there are multiple frequency ids present
    :type multi_id: bool
    :param selfreq: if there are multiple frequency ids, which one to load
    :type selfreq: int
    :param if_idx: 0-based indices of the IFs of the band in the original files
    :type if_idx: list of int
    :param default_refant: force the pipeline to choose this reference antenna by giving 
        its antenna code
    :type default_refant: str
    :param default_refant_list: list of prioritized antenna codes to use as reference antenna 
    :type default_refant_list: list of str
    :param search_central: for VLBA datasets, give priority to KP, LA, PT, OV, FD
    :type search_central: bool
    :param max_scan_refant_search: maximum number of scans per source where the SNR is 
        computed when looking for reference antenna
    :type max_scan_refant_search: int
    :param time_aver: time sampling threshold in seconds for time averaging
    :type time_aver: int
    :param freq_aver: channel width sampling threshold in kHz for frequency averaging
    :type freq_aver: int
    :param fringefit_snr: S/N threshold for the target fringe fit 
    :type fringefit_snr: float
    :param default_solint: solution interval for the science target fringe fit
    :type default_solint: int
    :param min_solint: minimum solution interval allowed for the science target fringe 
        fit
    :type min_solint: int
    :param max_solint: maximum solution interval allowed for the science target fringe 
        fit
    :type max_solint: int
    :param phase_ref: list of phase calibrator names for phase referencing
    :type phase_ref: list of str
    :param input_calibrator: force the pipeline to use this source as calibrator
    :type input_calibrator: str
    :param shift_coords: list of new coordinates for the targets, as Astropy SkyCoord 
        objects, in case a phase shift was necessary
    :type shift_coords: list of astropy.coordinates.SkyCoord
    :param load_antab: path of an external ANTAB file with amplitude calibration information
    :type load_antab: str
    :param load_flags: path of an external UVFLG file with initial flags
    :type load_flags: str
    :param channel_out: 'SINGLE' -> export one channel per IF, 'MULTI' -> export 
        multiple channels per IF
    :type channel_out: str
    :param flag_edge: fraction of the total channels to flag at the edge of each IF
    :type flag_edge: float
    :param interactive: produce interactive plots in the GUI
    :type interactive: bool
    :param stats_df: Pandas DataFrame where to keep track of the different statistics
    :type stats_df: pandas.DataFrame object
    """    
    ## PIPELINE STARTS
    t_i = time.time()

    # AIPS log is registered simultaneously for all science targets
    help.open_log(outpath_list, filename_list)

    # By default, sequence will start in 1
    seq = 1
        
    ## Check if the test file already exists and delete it ##
    uvdata = AIPSUVData(aips_name, klass, disk_number, seq)
    
    if uvdata.exists() == True:
        uvdata.zap()

    ## 1.- LOAD DATA ##
    disp.write_box(log_list, 'Loading data') 
    disp.print_box('Loading data')  
    #else:

    ## Load the dataset ##
    t0 = time.time()
    load.load_data(filepath_list, aips_name, sources, disk_number, multi_id,\
    selfreq, klass = klass, if_idx = if_idx, l_a = load_all, symlink_path = tmp_dir)
    ## Modify the AN table in case there are non ASCII characters   
    try:
        uvdata.antennas
    except SystemError:
        tabl.remove_ascii_antname(uvdata, filepath_list[0])
        tabl.remove_ascii_poltype(uvdata, filepath_list[0])
        print('\nAN Table was modified to correct for padding in entries.\n')
    
    # Print some general information
    disp.write_info(uvdata, filepath_list, log_list, sources, stats_df=stats_df)
    disp.print_info(uvdata, filepath_list, sources)

    # Record which IFs of the original files were loaded
    for pipeline_log in log_list:
        pipeline_log.write('\nIFs loaded from the original files: ' \
                           + ', '.join(str(i + 1) for i in if_idx) + '\n')

    t1 = time.time() 
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t1-t0))
    print('Execution time: {:.2f} s. \n'.format(t1-t0))
    stats_df['time_1'] = t1-t0

    ## Check data integrity
    print('\nChecking data integrity...\n')

    ## Check for order
    if uvdata.header['sortord'] != 'TB':
        load.tborder(uvdata)
        for pipeline_log in log_list:
            pipeline_log.write('\nData was not in TB order. It has been reordered using '\
                               + 'the UVSRT task\n')
        print('\nData was not in TB order. It has been reordered using ' \
              + 'the UVSRT task\n')
        
        stats_df['need_uvsrt'] = True
    else:
        stats_df['need_uvsrt'] = False
    
    ## Check for CL/NX tables
    if [1, 'AIPS CL'] not in uvdata.tables or [1, 'AIPS NX'] not in \
        uvdata.tables:
        load.run_indxr(uvdata)
        print('\nINDXR was run, NX#1 and CL#1 were created.\n')
            
        stats_df['need_indxr'] = True
    else:
        stats_df['need_indxr'] = False

    ## Check for TY/GC/FG tables
    missing_tables = False
    stats_df['need_ty'] = False
    stats_df['need_fg'] = False
    stats_df['need_gc'] = False
    stats_df['vlbacal_files'] = False
    stats_df['evncal_files'] = False
    stats_df['evnflag_files'] = False
    stats_df['ext_flag_file'] = False

    if load_antab != None:
        disp.write_box(log_list, 'Loading external table information')
        disp.print_box('Loading external table information')
        missing_tables = True
        t_i_table = time.time()
        stats_df['need_ty'] = False
        stats_df['need_gc'] = False
        stats_df['vlbacal_files'] = load_antab
        stats_df['evncal_files'] = load_antab
        tabl.load_external_antab(uvdata, load_antab)

        print(f'\nAmplitude calibration information has been loaded from {load_antab}\n')
        print('\nTY#1 and GC#1 created.\n')

        for pipeline_log in log_list:
                pipeline_log.write('\nAmplitude calibration information has been '\
                                   + f'loaded from {load_antab}'\
                                   + '\n\nTY#1 and GC#1 created.\n\n')

    elif uvdata.header.telescop == 'EVN':
        disp.write_box(log_list, 'Loading external table information')
        disp.print_box('Loading external table information')
        missing_tables = True
        t_i_table = time.time()

        need_fg = [1, 'AIPS FG'] not in uvdata.tables

        try:
            antab_url, flag_url, found_urls = tabl.load_evn_tables(uvdata, 
                                                                   load_flags=need_fg)
        except help.NoTablesError:
            # Without system temperatures the pipeline cannot continue
            msg = ('\nNo antab file was found in the EVN archive. '
                   'The pipeline will stop here.\n')
            print(msg)
            for pipeline_log in log_list:
                pipeline_log.write(msg)
            return(1)

        stats_df['evncal_files'] = antab_url

        msg = ''
        if len(found_urls) > 1:
            msg += '\nWARNING: several antab files found in the EVN archive:\n'
            for u in found_urls:
                msg += f'    {u}\n'
            msg += f'Using {antab_url}\n'

        msg += ('\nSystem temperatures and gain curves were retrieved from '
                f'{antab_url}\n\nTY#1 and GC#1 created.\n')

        if [1, 'AIPS GC'] not in uvdata.tables:
            msg += ('\nWARNING: the antab file contains no gain curve '
                    'information. No GC table was created.\n'
                    'The pipeline will stop here.\n')
            print(msg)
            for pipeline_log in log_list:
                pipeline_log.write(msg)
            return(1)

        if need_fg:
            stats_df['need_fg'] = True
            if flag_url is not None:
                stats_df['evnflag_files'] = flag_url
                msg += ('\nFlag information was not available in the file, '
                        f'it has been retrieved from {flag_url}\n\nFG#1 created.\n')
            else:
                stats_df['evnflag_files'] = None
                msg += ('\nNo flag file was found in the EVN archive. '
                        'No initial flags will be applied.\n')

        print(msg)
        for pipeline_log in log_list:
            pipeline_log.write(msg + '\n')

    else:
        if [1, 'AIPS TY'] not in uvdata.tables or [1, 'AIPS GC'] \
                not in uvdata.tables or [1, 'AIPS FG'] not in uvdata.tables:

            disp.write_box(log_list, 'Loading external table information')
            disp.print_box('Loading external table information')
            missing_tables = True
            t_i_table = time.time()

        if [1, 'AIPS TY'] not in uvdata.tables:
            try:
                retrieved_urls = tabl.load_ty_tables(uvdata)
            except help.NoTablesError:
                # If the pipeline finds no tables, stops here
                print("No vlba.cal tables were found online. The pipeline will stop here.\n")
                for pipeline_log in log_list:
                    pipeline_log.write("\nNo vlba.cal tables were found online. The pipeline will stop here.\n")

                return(1)

            for pipeline_log in log_list:
                for good_url in retrieved_urls:
                    pipeline_log.write('\nSystem temperatures were not available in the ' \
                                    + 'file, they have been retrieved from ' \
                                    + good_url)
                pipeline_log.write('\nTY#1 created.\n')

            # Move the temperature file to the target folders
            for path in outpath_list:
                shutil.copy(f'{tmp_dir}/tsys.vlba', path + '/TABLES/tsys.vlba')

            # Clean the tmp directory
            os.system(f'rm {tmp_dir}/*.vlba')

            for good_url in retrieved_urls:
                print('\nSystem temperatures were not available in the ' \
                                        + 'file, they have been retrieved from \n' \
                                        + good_url)
            print('\nTY#1 created.\n')
            stats_df['need_ty'] = True
            stats_df['vlbacal_files'] = str(retrieved_urls)

        if [1, 'AIPS GC'] not in uvdata.tables:
            good_url = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/vlba_gains.key'
            try:
                tabl.load_gc_tables(uvdata)
            except help.NoTablesError:
                for pipeline_log in log_list:
                    pipeline_log.write('WARNING: No gain curves were found at the '\
                                        + 'observed date. No GC table will be created.\n')
                print('WARNING: No gain curves were found at the observed date. No ' \
                + 'GC table will be created.\nThe pipeline will stop here.\n')

                return(1)  # END THE PIPELINE!

            for pipeline_log in log_list:
                pipeline_log.write('\nGain curve information was not available in the '\
                                + 'file, it has been retrieved from\n' + good_url \
                                + '\n\nGC#1 created.\n\n')

            # Move the gain curve file to the target folders
            for path in outpath_list:
                shutil.copy(f'{tmp_dir}/gaincurves.vlba', path + '/TABLES/gaincurves.vlba')

            # Clean the tmp directory
            os.system(f'rm {tmp_dir}/*.vlba')

            print('\nGain curve information was not available in the file, it has '\
            + 'been retrieved from\n' + good_url + '\n\nGC#1 created.\n')
            stats_df['need_gc'] = True

    if [1, 'AIPS FG'] not in uvdata.tables and uvdata.header.telescop != 'EVN':
        try:
            retrieved_urls = tabl.load_fg_tables(uvdata)
            for pipeline_log in log_list:
                for good_url in retrieved_urls:
                    pipeline_log.write('Flag information was not available in the file, ' \
                                        + 'it has been retrieved from ' + good_url + '\n')
                pipeline_log.write('FG#1 created.\n')

            # Move the flag file to the target folders
            for path in outpath_list:
                shutil.copy(f'{tmp_dir}/flags.vlba', path + '/TABLES/flags.vlba')

            # Clean the tmp directory
            os.system(f'rm {tmp_dir}/*.vlba')

            for good_url in retrieved_urls:
                print('Flag information was not available in the file, ' \
                                + 'it has been retrieved from\n' + good_url + '\n')
            print('FG#1 created.\n')
            stats_df['need_fg'] = True
            stats_df['vlbacal_files'] = str(retrieved_urls)

        except help.NoTablesError:
            # If the pipeline finds no tables, gives a warning but continues
            print("No vlba.cal tables were found online. No initial flags will be applied.\n")
            for pipeline_log in log_list:
                pipeline_log.write("\nNo vlba.cal tables were found online. No initial flags will be applied.\n")
            stats_df['need_fg'] = True
            stats_df['vlbacal_files'] = None

    if load_flags != None:
        disp.write_box(log_list, 'Loading external flag information')
        disp.print_box('Loading external flag information')
        t_i_flags = time.time()
        stats_df['ext_flag_file'] = load_flags
        had_fg = [1, 'AIPS FG'] in uvdata.tables
        tabl.load_external_flags(uvdata, load_flags)

        # Keep a copy of the flag file with the rest of the tables
        for path in outpath_list:
            shutil.copy(load_flags, path + '/TABLES/')

        msg = f'\nFlag information has been loaded from {load_flags}\n'
        if had_fg:
            msg += '\nThe flags were added to the existing FG#1.\n'
        else:
            msg += '\nFG#1 created.\n'
        msg += '\nExecution time: {:.2f} s.\n'.format(time.time() - t_i_flags)
        print(msg)
        for pipeline_log in log_list:
            pipeline_log.write(msg)

    if missing_tables == True:
        t1 = time.time()
        for pipeline_log in log_list:
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t1-t_i_table))

    stats_df['time_2'] = time.time()-t1

    ## If multi-id, check if the source is in this id
    if multi_id == True:
        obs_source_ids = [x.source_id for x in uvdata.table('NX', 1)]
        obs_source_names = set([y.source.strip() for y in uvdata.table('SU', 1) 
                            if y.id__no in obs_source_ids])
        if len(set(target_list).intersection(obs_source_names)) != len(set(target_list)): 
            miss_sources = [x for x in target_list if x not in obs_source_names]
            print("\nNot all targets were observed at this frequency, the pipeline will stop here.\n")
            print(f"\nMissing sources: {miss_sources}\n")
            for pipeline_log in log_list:
                pipeline_log.write("\nNot all targets were observed at this frequency, the pipeline will stop here.\n")
                pipeline_log.write(f"\nMissing sources: {miss_sources}\n")
            return()


    ## Shift phase center if necessary ##
    
    if shift_coords != None:
        t_shift = time.time()
        disp.write_box(log_list, 'Shifting phase center')
        disp.print_box('Shifting phase center')
        for i, target in enumerate(target_list):
            if shift_coords[i] == None:
                stats_df.at[i, 'uvshift'] = False
                stats_df.at[i, 'time_3'] = 0
                old_coord = shft.get_coord(uvdata, target)
                stats_df.at[i, 'old_coords'] = old_coord.to_string(style = 'hmsdms')
                stats_df.at[i, 'new_coords'] = old_coord.to_string(style = 'hmsdms')
                continue
                
            stats_df.at[i, 'uvshift'] = True
            old_seq = uvdata.seq    
            # Delete the data if it already existed
            if AIPSUVData(uvdata.name, uvdata.klass, \
                          uvdata.disk, uvdata.seq + 1).exists(): 
                AIPSUVData(uvdata.name, uvdata.klass, \
                          uvdata.disk, uvdata.seq + 1).zap()
            # Shift
            old_coord, new_coord = shft.uv_shift(uvdata, target, shift_coords[i])
         
            uvdata = AIPSUVData(uvdata.name, uvdata.klass, \
                                uvdata.disk, old_seq + 1)

            # Remove previous dataset
            AIPSUVData(uvdata.name, uvdata.klass, \
                                uvdata.disk, uvdata.seq - 1).zap()
            
            log_list[i].write('\nThe new coordinates for the phase center of ' + target \
                              + ' are: ' + shift_coords[i].to_string(style = 'hmsdms') \
                              + '\n')
            print('\nThe new coordinates for the phase center of ' + target \
                              + ' are: ' + shift_coords[i].to_string(style = 'hmsdms') \
                              + '\n')
            
            stats_df.at[i, 'old_coords'] = old_coord.to_string(style = 'hmsdms')
            stats_df.at[i, 'new_coords'] = new_coord.to_string(style = 'hmsdms')
            stats_df.at[i, 'time_3'] = time.time() - t_shift

    else:
        stats_df['time_3'] = 0
        stats_df['uvshift'] = False
        for i, target in enumerate(target_list):
            old_coord = shft.get_coord(uvdata, target)
            stats_df.at[i, 'old_coords'] = old_coord.to_string(style = 'hmsdms')
            stats_df.at[i, 'new_coords'] = old_coord.to_string(style = 'hmsdms')

    # Update the sequence
    seq = uvdata.seq
    
    t_avg = time.time()
    ## If the time resolution is < 2s, average the dataset in time 
    ## (unless other value is given)
    if [1, 'AIPS CQ'] in uvdata.tables:
        try:
            time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'][0])
        except TypeError: # Single IF datasets
            time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'])
    else:
        wuvdata = wizard.AIPSUVData(uvdata.name, uvdata.klass, uvdata.disk, uvdata.seq)
        time_resol = float(round(min([x.inttim for x  in wuvdata]), 2))
        
    if time_resol <= (time_aver/1.99):
        avgdata = AIPSUVData(aips_name[:9] + '_AT', uvdata.klass, disk_number, seq)
        if avgdata.exists() == True:
            avgdata.zap()
        load.time_aver(uvdata, time_resol, time_aver)
        uvdata = AIPSUVData(aips_name[:9] + '_AT', uvdata.klass, disk_number, seq)

        # Index the data again
        uvdata.zap_table('CL', 1)
        load.run_indxr(uvdata)

        disp.write_box(log_list, 'Data averaging')
        disp.print_box('Data averaging')
        for pipeline_log in log_list:
            pipeline_log.write('\nThe time resolution was ' \
                            + '{:.2f}'.format(time_resol) \
                            + f's. It has been averaged to {time_aver}s.\n')
        print('\nThe time resolution was {:.2f}'.format(time_resol) \
            + f's. It has been averaged to {time_aver}s.')
        is_data_avg = True
        stats_df['time_avg'] = True
        stats_df['old_timesamp'] = time_resol
        stats_df['new_timesamp'] = time_aver
    else:
        is_data_avg = False
        stats_df['time_avg'] = False
        stats_df['old_timesamp'] = time_resol
        stats_df['new_timesamp'] = time_resol
        
            
    ## If the channel bandwidth is smaller than 0.5 MHz, average the dataset 
    ## in frequency up to 0.5 MHz per channel (unless other value is given)
    if [1, 'AIPS CQ'] in uvdata.tables:
        try:
            ch_width = float(uvdata.table('CQ', 1)[0]['chan_bw'][0])
            no_chan = int(uvdata.table('CQ', 1)[0]['no_chan'][0])
        except TypeError: # Single IF datasets
            ch_width = float(uvdata.table('CQ', 1)[0]['chan_bw'])
            no_chan = int(uvdata.table('CQ', 1)[0]['no_chan'])
        
    else:
        try:
            ch_width = float(uvdata.table('FQ', 1)[0]['ch_width'][0])
            total_width = float(uvdata.table('FQ', 1)[0]['total_bandwidth'][0])
            no_chan = int(total_width/ch_width)
        except TypeError: # Single IF datasets
            ch_width = float(uvdata.table('FQ', 1)[0]['ch_width'])
            total_width = float(uvdata.table('FQ', 1)[0]['total_bandwidth'])
            no_chan = int(total_width/ch_width)

    if ch_width < freq_aver*1000:
        if is_data_avg == False:
            avgdata = AIPSUVData(aips_name[:9] + '_AF', uvdata.klass, \
                                 disk_number, seq)
            if avgdata.exists() == True:
                avgdata.zap()
            f_ratio = freq_aver*1000/ch_width    # NEED TO ADD A CHECK IN CASE THIS FAILS
            
            if time_resol >= 0.33: # => If it was not written before
                disp.write_box(log_list, 'Data averaging')
                disp.print_box('Data averaging')
            
            load.freq_aver(uvdata,f_ratio)
            uvdata = AIPSUVData(aips_name[:9] + '_AF', uvdata.klass, \
                                 disk_number, seq)

        if is_data_avg == True:
            avgdata = AIPSUVData(aips_name[:9] + '_ATF', uvdata.klass, \
                                 disk_number, seq)
            if avgdata.exists() == True:
                avgdata.zap()
            f_ratio = freq_aver*1000/ch_width    # NEED TO ADD A CHECK IN CASE THIS FAILS
            
            load.freq_aver(uvdata,f_ratio)
            uvdata = AIPSUVData(aips_name[:9] + '_ATF', uvdata.klass, \
                                 disk_number, seq)

        # Index the data again
        uvdata.zap_table('CL', 1)
        load.run_indxr(uvdata)

        try:
            no_chan_new = int(uvdata.table('FQ', 1)[0]['total_bandwidth'][0]/ \
                              uvdata.table('FQ', 1)[0]['ch_width'][0])
        except TypeError: # Single IF datasets
            no_chan_new = int(uvdata.table('FQ', 1)[0]['total_bandwidth']/ \
                              uvdata.table('FQ', 1)[0]['ch_width'])


        for pipeline_log in log_list:
            pipeline_log.write('\nThere were ' + str(no_chan) + ' channels of ' \
                            + str(ch_width/1e3) + ' kHz per IF. The dataset has ' \
                            + 'been averaged to ' + str(no_chan_new) + ' channels of ' \
                            + '500 kHz.\n')

        print('\nThere were ' + str(no_chan) + ' channels of ' \
              + str(ch_width/1e3) + ' kHz per IF. The dataset has ' \
              + 'been averaged to ' + str(no_chan_new) + ' channels of ' \
              + f'{freq_aver} kHz.\n')
        
        stats_df['freq_avg'] = True
        stats_df['old_ch_width'] = ch_width
        stats_df['old_ch_no'] = no_chan
        stats_df['new_ch_width'] = freq_aver*1000
        stats_df['new_ch_no'] = no_chan_new
        
    else:
        stats_df['freq_avg'] = False
        stats_df['old_ch_width'] = ch_width
        stats_df['old_ch_no'] = no_chan
        stats_df['new_ch_width'] = ch_width
        stats_df['new_ch_no'] = no_chan
        
    stats_df['time_4'] = time.time() - t_avg

    ## Print scan information ##    
    load.print_listr(uvdata, outpath_list, filename_list)
    for i, pipeline_log in enumerate(log_list):
        pipeline_log.write('\nScan information printed in '  \
                            + filename_list[i] + '_scansum.txt \n')
        
    # Counting scans and scan length
    nx_table = uvdata.table('NX', 1)
    for i, target in enumerate(target_list):
        s_count = 0
        s_lengths = []
        target_id = [x.id for x in full_source_list if x.name == target][0]
        for scan in nx_table:
            if scan.source_id == target_id:
                s_count += 1
                s_lengths.append(round(scan.time_interval * 24 * 3600,1))
        stats_df.at[i, 'n_scans'] = s_count
        stats_df.at[i, 'scan_lengths'] = str(s_lengths)

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=1, flagver=1, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl1 = AIPSUVData(target, 'PLOT', uvdata.disk, 1)
        vis_cl1, vis_ant_cl1 = expo.vis_count_v2(cl1)
        stats_df.at[i, 'CL1_vis'] = int(vis_cl1)
        stats_df.at[i, 'CL1_ant_vis'] = json.dumps(vis_ant_cl1)
        print(f"CL1 visibilities of {target}: {vis_cl1}{disp.vis_frac(vis_cl1, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL1 visibilities of {target}: {vis_cl1}{disp.vis_frac(vis_cl1, stats_df.at[i, 'CL1_vis'])}\n")
    
    ## Smooth the TY table ##  
    ## Flag antennas with no TY or GC table entries ##  
    
    t_tsys = time.time()
    disp.write_box(log_list, 'Flagging system temperatures')
    disp.print_box('Flagging system temperatures')
    
    no_tsys_ant, no_gc_ant = tysm.ty_smooth(uvdata)

    if len(no_tsys_ant) > 0:
        for n in no_tsys_ant:
            n_name = [x['anname'] for x in uvdata.table('AN', 1) if x['nosta'] == n] 
            n_name[0] = n_name[0].replace(' ','') 
            print('\n' + str(n) + '-' + n_name[0] + ' has no TSys available, ' \
                  + 'it will be flagged.\n')
                
        for pipeline_log in log_list:
            for n in no_tsys_ant:
                n_name = [x['anname'] for x in uvdata.table('AN', 1) if x['nosta'] == n]
                n_name[0] = n_name[0].replace(' ','') 
                pipeline_log.write('\n' + str(n) + '-' + n_name[0] + ' has no Tsys ' \
                                   + 'available, it will be flagged.\n') 

    if len(no_gc_ant) > 0:
        for n in [x for x in no_gc_ant if x not in no_tsys_ant]:
            n_name = [x['anname'] for x in uvdata.table('AN', 1) if x['nosta'] == n] 
            n_name[0] = n_name[0].replace(' ','') 
            print('\n' + str(n) + '-' + n_name[0] + ' has no gain curve available, ' \
                  + 'it will be flagged.\n')
            
        for pipeline_log in log_list:
            for n in [x for x in no_gc_ant if x not in no_tsys_ant]:
                n_name = [x['anname'] for x in uvdata.table('AN', 1) if x['nosta'] == n]
                n_name[0] = n_name[0].replace(' ','') 
                pipeline_log.write('\n' + str(n) + '-' + n_name[0] + ' has no gain ' \
                                   + 'curve available, it will be flagged.\n') 
    
    original_tsys, flagged_tsys, tsys_dict, smo_antennas = tysm.ty_assess(uvdata)
    
    tsys_flag_percent = np.round(flagged_tsys/original_tsys*100, 2)

    for pipeline_log in log_list:
        pipeline_log.write("\nAntenna |  TY1  |  TY2 \n")
        pipeline_log.write("--------|-------|-------\n")
        for _, (ant, ty2, ty1) in tsys_dict.items():
            if ty1 != 0:
                pipeline_log.write(f"{ant.strip():<8}|  {ty1:<4} |  {ty2} \n")

        if len(smo_antennas) > 0:
            pipeline_log.write(f"\nSystem temperatures of {smo_antennas} were fully flagged."\
                + " The antennas will be included in FG#2.\n")

        pipeline_log.write('\nSystem temperatures clipped: ' + str(tsys_flag_percent) \
                           + '% of the Tsys values have been flagged ('  \
                           + str(flagged_tsys) + '/' + str(original_tsys) + ')\n' \
                           + 'TY#2 created.\n')
        
    print("\nAntenna |  TY1  |  TY2 \n")
    print("--------|-------|-------\n")
    for _, (ant, ty2, ty1) in tsys_dict.items():
        if ty1 != 0:
            print(f"{ant.strip():<8}|  {ty1:<4} |  {ty2} \n")

    if len(smo_antennas) > 0:
        print(f"\nSystem temperatures of {smo_antennas} were fully flagged."\
              + " The antennas will be included in FG#2.\n")
     
    print('\nSystem temperatures clipped: ' + str(tsys_flag_percent) \
            + '% of the Tsys values have been flagged ('  \
            + str(flagged_tsys) + '/' + str(original_tsys) + ')\n' \
            + 'TY#2 created.\n') 
    
    # Print the TY tables
    try:
        for i, target in enumerate(target_list):
            plot.tsys_plotter(outpath_list[i], uvdata, tyver = 1)
            print('\nOriginal system temperatures plotted in '
                    + outpath_list[i] + '/PLOTS/'  \
                    + filename_list[i] + '_TSYS_TY1.pdf\n')
            log_list[i].write('\nOriginal system temperatures plotted in '
                            + outpath_list[i] + '/PLOTS/'  \
                            + filename_list[i] + '_TSYS_TY1.pdf\n')           
    except RuntimeError:
        for i, target in enumerate(target_list):
            log_list[i].write('\nOriginal system temperatures could not be plotted.\n')
        print('\nOriginal system temperatures could not be plotted.\n')

    try:
        for i, target in enumerate(target_list):
            plot.tsys_plotter(outpath_list[i], uvdata, tyver = 2)
            print('\nSmoothed system temperatures plotted in '
                    + outpath_list[i] + '/PLOTS/'  \
                    + filename_list[i] + '_TSYS_TY2.pdf\n')
            log_list[i].write('\nSmoothed system temperatures plotted in '
                            + outpath_list[i] + '/PLOTS/'  \
                            + filename_list[i] + '_TSYS_TY2.pdf\n')           
    except RuntimeError:
        for i, target in enumerate(target_list):
            log_list[i].write('\nSmoothed system temperatures could not be plotted.\n')
        print('\nSmoothed system temperatures could not be plotted.\n')

    
    stats_df['ty1_points'] = original_tsys
    stats_df['ty2_points'] = original_tsys - flagged_tsys
    stats_df['tsys_dict'] = json.dumps(tsys_dict)

    # Remove unflagged splitted entries
    for i, target in enumerate(target_list):
        AIPSUVData(target, 'PLOT', uvdata.disk, 1).zap()

    # Counting again the visibilities with the flags
    expo.data_split(uvdata, target_list, cl_table=1, flagver=2, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl1_fg2 = AIPSUVData(target, 'PLOT', uvdata.disk, 1)
        vis_cl1_fg2, vis_ant_cl1_fg2 = expo.vis_count_v2(cl1_fg2)
        stats_df.at[i, 'CL1_vis_FG2'] = int(vis_cl1_fg2)
        stats_df.at[i, 'CL1_FG2_ant_vis'] = json.dumps(vis_ant_cl1_fg2)
        print(f"CL1 visibilities of {target} after flagging: {vis_cl1_fg2}{disp.vis_frac(vis_cl1_fg2, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL1 visibilities of {target} after flagging: {vis_cl1_fg2}{disp.vis_frac(vis_cl1_fg2, stats_df.at[i, 'CL1_vis'])}\n")

    t2 = time.time()

    stats_df['time_5'] = t2 - t_tsys
    
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t2-t1))
    print('Execution time: {:.2f} s. \n'.format(t2-t1))

    # full_source_list needs to be re-written after loading, to avoid issues when 
    # concatenating files
    full_source_list = load.redo_source_list(uvdata)

    ## Choose refant ##
    disp.write_box(log_list, 'Reference antenna search')
    disp.print_box('Reference antenna search')
    print('\nSearch for reference antenna starts...\n')

    # Disable search central antennas if the telescope is not the VLBA
    if uvdata.header.telescop != 'VLBA':
        search_central = False
    
    if default_refant == None:
        for pipeline_log in log_list:
            pipeline_log.write('\nChoosing reference antenna with all sources.\n')

        try:
            refant, ant_dict = rant.refant_choose_snr(uvdata, sources, target_list, 
                            full_source_list, log_list, search_central=search_central, 
                            max_scans = max_scan_refant_search)
        except ValueError:
            print('\n\nNO ANTENNAS!\n\n')
            return()


        refant_summary = (
            f"\n{ant_dict[refant].codename} has been selected as the reference antenna "
            f"with an SNR of {round(ant_dict[refant].median_SNR, 2)}. It is available in "
            f"{len(ant_dict[refant].scans_obs)} out of {ant_dict[refant].max_scans} scans.\n"
        )

        for pipeline_log in log_list:
            pipeline_log.write(refant_summary)
            pipeline_log.write("Antenna  |   SNR   | Obs Scans | Tot Scans\n")
            pipeline_log.write("---------|---------|-----------|-----------\n")
            for ant in ant_dict.values():
                pipeline_log.write(
                    f"{ant.codename:<8} | {round(ant.median_SNR,2):>6} |"
                    f" {len(ant.scans_obs):>9} | {ant.max_scans:>9}\n"
                )

        # Console output
        print(refant_summary)
        print("Antenna  |   SNR   | Obs Scans | Tot Scans")
        print("---------|---------|-----------|-----------")
        for ant in ant_dict.values():
            print(
                f"{ant.codename:<8} | {round(ant.median_SNR,2):>6} |"
                f" {len(ant.scans_obs):>9} | {ant.max_scans:>9}"
            )

        stats_df['refant_no'] = refant
        stats_df['refant_name'] = ant_dict[refant].name
        refant_rank = dict(zip([x.name for x in ant_dict.values()], 
                               [x.median_SNR for x in ant_dict.values()]))
        stats_df['refant_rank'] = json.dumps(refant_rank)

    else:
        refant = [x['nosta'] for x in uvdata.table('AN',1) \
                  if default_refant in x['anname']][0]
        for pipeline_log in log_list:
            pipeline_log.write('\n' + default_refant + ' has been manually selected as the ' \
                               + 'reference antenna.\n')
        print(default_refant + ' has been manually selected as the reference antenna.\n')

        stats_df['refant_no'] = refant
        stats_df['refant_name'] = default_refant
        stats_df['refant_rank'] = json.dumps({default_refant: 'MANUAL'})


    if default_refant == None and default_refant_list == None:
        priority_refant_names = [x.name for x in ant_dict.values()][1:]
        priority_refants = []
        for name in priority_refant_names:
            priority_refants.append([x['nosta'] for x in uvdata.table('AN', 1)\
                                     if name in x['anname']][0])

    elif default_refant_list != None:
        priority_refants = []
        for name in default_refant_list:
            priority_refants.append([x['nosta'] for x in uvdata.table('AN', 1)\
                                     if name in x['anname']][0])
            
    elif default_refant != None and default_refant_list == None:
        priority_refants = []

    t3=time.time()
    stats_df['time_6'] = t3-t2
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t3-t2))
    print('Execution time: {:.2f} s. \n'.format(t3-t2))

    ## Ionospheric correction ##
    disp.write_box(log_list, 'Ionospheric corrections')
    disp.print_box('Ionospheric corrections')
    
    YYYY = int(uvdata.header.date_obs[:4])
    MM = int(uvdata.header.date_obs[5:7])
    DD = int(uvdata.header.date_obs[8:])
    date_obs = datetime(YYYY, MM, DD)
    if date_obs > datetime(1998,6,1):
        
        files = iono.ionos_correct(uvdata)

        for pipeline_log in log_list:
            pipeline_log.write('\nIonospheric corrections applied!\nCL#2 created.'\
                            + '\n')
        print('\nIonospheric corrections applied!\nCL#2 created.\n')

        # Counting visibilities
        expo.data_split(uvdata, target_list, cl_table=2, flagver=2, flag_frac = flag_edge)
        for i, target in enumerate(target_list):
            cl2 = AIPSUVData(target, 'PLOT', uvdata.disk, 2)
            vis_cl2, vis_ant_cl2 = expo.vis_count_v2(cl2)
            stats_df.at[i, 'CL2_vis'] = int(vis_cl2)
            stats_df.at[i, 'CL2_ant_vis'] = json.dumps(vis_ant_cl2) 
            print(f"CL2 visibilities of {target}: {vis_cl2}{disp.vis_frac(vis_cl2, stats_df.at[i, 'CL1_vis'])}\n")
            log_list[i].write(f"\nCL2 visibilities of {target}: {vis_cl2}{disp.vis_frac(vis_cl2, stats_df.at[i, 'CL1_vis'])}\n")

        t4 = time.time()

        os.system(f'rm -rf {tmp_dir}/jplg*')
        os.system(f'rm -rf {tmp_dir}/codg*')

        stats_df['iono_files'] = str(files)
        stats_df['time_7'] = t4 - t3
        

    else:

        help.tacop(uvdata, 'CL', 1, 2)
        for pipeline_log in log_list:
            pipeline_log.write('\nIonospheric corrections not applied! IONEX '\
                            + 'files are not available for observations '\
                            + 'older than June 1998.\nCL#2 will be copied '\
                            + 'from CL#1.\n')
        print('\nIonospheric corrections not applied! IONEX files are not '\
              + 'available for observations older than June 1998.\nCL#2 '\
              + 'will be copied from CL#1.\n')
        
        # Counting visibilities
        expo.data_split(uvdata, target_list, cl_table=2, flagver=2, flag_frac = flag_edge)
        for i, target in enumerate(target_list):
            cl2 = AIPSUVData(target, 'PLOT', uvdata.disk, 2)
            vis_cl2, vis_ant_cl2 = expo.vis_count_v2(cl2)
            stats_df.at[i, 'CL2_vis'] = int(vis_cl2)
            stats_df.at[i, 'CL2_ant_vis'] = json.dumps(vis_ant_cl2)
            print(f"CL2 visibilities of {target}: {vis_cl2}{disp.vis_frac(vis_cl2, stats_df.at[i, 'CL1_vis'])}\n")
            log_list[i].write(f"\nCL2 visibilities of {target}: {vis_cl2}{disp.vis_frac(vis_cl2, stats_df.at[i, 'CL1_vis'])}\n")

        t4 = time.time()

        stats_df['iono_files'] = 'OLD'
        stats_df['time_7'] = t4 - t3

    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t4-t3))
    print('Execution time: {:.2f} s. \n'.format(t4-t3)) 

    ## Earth orientation parameters correction ##
    disp.write_box(log_list, 'Earth orientation parameters corrections')
    disp.print_box('Earth orientation parameters corrections')

    with fits.open(filepath_list[0]) as hdul:
        try:
            if hdul[0].header['CORRELAT'].strip() == 'SFXC':
                for pipeline_log in log_list:
                    pipeline_log.write('\nEarth orientation parameter corrections cannot '\
                                    + 'be applied for non-DiFX correlators.\n'\
                                    + 'CL#3 will be copied from CL#2.\n')
                    print('\nEarth orientation parameter corrections cannot be ' \
                                    + 'applied for non-DiFX correlators.\n'\
                                    + 'CL#3 will be copied from CL#2.\n')
                help.tacop(uvdata, 'CL', 2, 3)
            else:
                eopc.eop_correct(uvdata)

                for pipeline_log in log_list:
                    pipeline_log.write('\nEarth orientation parameter corrections applied!\n'\
                                    + 'CL#3 created.\n')
                print('\nEarth orientation parameter corrections applied!\nCL#3 created.\n')
                os.system(f'rm -rf {tmp_dir}/usno*')

        except KeyError:
            # Check if it's an EVN observation
            if uvdata.header.telescop == 'EVN':
                for pipeline_log in log_list:
                    pipeline_log.write('\nEarth orientation parameter corrections are '\
                                    + 'not applied for EVN observations.\n'\
                                    + 'CL#3 will be copied from CL#2.\n')
                    print('\nEarth orientation parameter corrections are '\
                                    + 'not applied for EVN observations.\n'\
                                    + 'CL#3 will be copied from CL#2.\n')
                help.tacop(uvdata, 'CL', 2, 3)
            else:
                try:
                    _ = len(uvdata.table('CT', 1))
                    eopc.eop_correct(uvdata)

                    for pipeline_log in log_list:
                        pipeline_log.write('\nEarth orientation parameter corrections applied!\n'\
                                        + 'CL#3 created.\n')
                    print('\nEarth orientation parameter corrections applied!\nCL#3 created.\n')
                    os.system(f'rm -rf {tmp_dir}/usno*')

                except TypeError:
                    for pipeline_log in log_list:
                        pipeline_log.write('\nEarth orientation parameter corrections cannot '\
                                        + 'be applied. CT table is not compatible.\n'\
                                        + 'CL#3 will be copied from CL#2.\n')
                        print('\nEarth orientation parameter corrections cannot be ' \
                                        + 'applied. CT table is not compatible.\n'\
                                        + 'CL#3 will be copied from CL#2.\n')
                    help.tacop(uvdata, 'CL', 2, 3)



    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=3, flagver=2, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl3 = AIPSUVData(target, 'PLOT', uvdata.disk, 3)
        vis_cl3, vis_ant_cl3 = expo.vis_count_v2(cl3)
        stats_df.at[i, 'CL3_vis'] = int(vis_cl3)
        stats_df.at[i, 'CL3_ant_vis'] = json.dumps(vis_ant_cl3)
        print(f"CL3 visibilities of {target}: {vis_cl3}{disp.vis_frac(vis_cl3, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL3 visibilities of {target}: {vis_cl3}{disp.vis_frac(vis_cl3, stats_df.at[i, 'CL1_vis'])}\n")

    t5 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t5-t4))
    print('Execution time: {:.2f} s. \n'.format(t5-t4))

    stats_df['time_8'] = t5 - t4

    ## Parallatic angle correction ##
    disp.write_box(log_list, 'Parallactic angle corrections')
    disp.print_box('Parallactic angle corrections')
    
    pang.pang_corr(uvdata)

    for pipeline_log in log_list:
        pipeline_log.write('\nParallactic angle corrections applied!\nCL#4'\
                        + ' created.\n')
    print('\nParallactic angle corrections applied!\nCL#4 created.\n')

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=4, flagver=2, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl4 = AIPSUVData(target, 'PLOT', uvdata.disk, 4)
        vis_cl4, vis_ant_cl4 = expo.vis_count_v2(cl4)
        stats_df.at[i, 'CL4_vis'] = int(vis_cl4)
        stats_df.at[i, 'CL4_ant_vis'] = json.dumps(vis_ant_cl4)
        print(f"CL4 visibilities of {target}: {vis_cl4}{disp.vis_frac(vis_cl4, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL4 visibilities of {target}: {vis_cl4}{disp.vis_frac(vis_cl4, stats_df.at[i, 'CL1_vis'])}\n")

    t6 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t6-t5))
    print('Execution time: {:.2f} s. \n'.format(t6-t5))

    stats_df['time_9'] = t6 - t5

    ## Selecting calibrator scan ##
    # If there is no input calibrator
    if input_calibrator == None:
        ## Look for calibrator ##
        ## SNR fringe search ##
        disp.write_box(log_list, 'Calibrator search')
        disp.print_box('Calibrator search')
        
        #snr_fring(uvdata, refant)
        cali.snr_fring(uvdata, refant, priority_refants)
        
        ## Get a list of scans ordered by SNR ##
        try:
            scan_list = cali.snr_scan_list_v2(uvdata)
        except help.NoScansError:
            for pipeline_log in log_list:
                pipeline_log.write('\nNone of the scans reached a minimum SNR of ' \
                                + '5 and the dataset could not be automatically ' \
                                + 'calibrated.\nThe pipeline will stop now.\n')
                
            print('\nNone of the scans reached a minimum SNR of ' \
                + '5 and the dataset could not be automatically ' \
                + 'calibrated.\nThe pipeline will stop now.\n')
                
            return()
        
        ## Get the calibrator scans
        calibrator_scans, no_calib_antennas = cali.get_calib_scans(uvdata, scan_list, refant)

        t7 = time.time()

        # This needs to be managed better
        if len(calibrator_scans) == 0:
            print("\n\nNo suitable calibrators were found, the pipeline will end now\n\n")
            for pipeline_log in log_list:
                pipeline_log.write("\n\nNo suitable calibrators were found, the pipeline will end now\n\n")
            return()

        for pipeline_log in log_list:
            if len(calibrator_scans) == 1:
                scan_i = help.ddhhmmss(calibrator_scans[0].time - calibrator_scans[0].time_interval / 2)
                scan_f = help.ddhhmmss(calibrator_scans[0].time + calibrator_scans[0].time_interval / 2)
                init_str = f"{scan_i[0]:02}/{scan_i[1]:02}:{scan_i[2]:02}:{scan_i[3]:02}"
                fin_str  = f"{scan_f[0]:02}/{scan_f[1]:02}:{scan_f[2]:02}:{scan_f[3]:02}"

                antennas = [str(a['nosta']) +  '-' + a['anname'].strip() for a in uvdata.table('AN', 1) 
                            if a['nosta'] in calibrator_scans[0].calib_antennas[:-1]]
                antennas = list(dict.fromkeys(antennas)) # Remove duplicates
                flagged_antennas = [str(a['nosta']) +  '-' + a['anname'].strip() for a in uvdata.table('AN', 1) 
                            if a['nosta'] in no_calib_antennas]
                flagged_antennas = list(dict.fromkeys(flagged_antennas)) # Remove duplicates
                
                pipeline_log.write(f"\n{'Source:':<12} {calibrator_scans[0].source_name}\t\t")
                pipeline_log.write(f"\n{'Time:':<12} {init_str} - {fin_str}")
                pipeline_log.write(f"\n{'Antennas:':<12} {antennas}\t\t")
                pipeline_log.write(f"\n{'Mean SNR:':<12} {calibrator_scans[0].calib_snr}\n")
                if len(no_calib_antennas) > 0:
                    pipeline_log.write(f"\nThere were no fringes with SNR > 5 to antennas: {flagged_antennas},\n")
                    pipeline_log.write(f"They will be flagged.\n\n")
                    pipeline_log.write('FG#3 created.\n')
                pipeline_log.write('\nSN#1 created.\n')



            else:
                pipeline_log.write('\nThe chosen scans for calibration are:\n')
                for scn in calibrator_scans:   
                    scan_i = help.ddhhmmss(scn.time - scn.time_interval / 2)
                    scan_f = help.ddhhmmss(scn.time + scn.time_interval / 2)
                    init_str = f"{scan_i[0]:02}/{scan_i[1]:02}:{scan_i[2]:02}:{scan_i[3]:02}"
                    fin_str  = f"{scan_f[0]:02}/{scan_f[1]:02}:{scan_f[2]:02}:{scan_f[3]:02}"

                    antennas = [str(a['nosta']) +  '-' + a['anname'].strip() for a in uvdata.table('AN', 1) 
                                if a['nosta'] in scn.calib_antennas[:-1]]
                    antennas = list(dict.fromkeys(antennas)) # Remove duplicates
                    flagged_antennas = [str(a['nosta']) +  '-' + a['anname'].strip() for a in uvdata.table('AN', 1) 
                                if a['nosta'] in no_calib_antennas]
                    flagged_antennas = list(dict.fromkeys(flagged_antennas)) # Remove duplicates

                    pipeline_log.write(f"\n{'Source:':<12} {scn.source_name}\t\t")
                    pipeline_log.write(f"\n{'Time:':<12} {init_str} - {fin_str}")
                    pipeline_log.write(f"\n{'Antennas:':<12} {antennas}\t\t")
                    pipeline_log.write(f"\n{'Mean SNR:':<12} {scn.calib_snr}\n")
                if len(no_calib_antennas) > 0:
                    pipeline_log.write(f"\nThere were no fringes with SNR > 5 to antennas: {flagged_antennas},\n")
                    pipeline_log.write(f"They will be flagged.\n\n")
                    pipeline_log.write('FG#3 created.\n')
                pipeline_log.write('\nSN#1 created.\n')

            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t7-t6))

   
        if len(calibrator_scans) == 1:          
            print('\nThe chosen scan for calibration is:\n')
            scan_i = help.ddhhmmss(calibrator_scans[0].time - calibrator_scans[0].time_interval / 2)
            scan_f = help.ddhhmmss(calibrator_scans[0].time + calibrator_scans[0].time_interval / 2)
            init_str = f"{scan_i[0]:02}/{scan_i[1]:02}:{scan_i[2]:02}:{scan_i[3]:02}"
            fin_str  = f"{scan_f[0]:02}/{scan_f[1]:02}:{scan_f[2]:02}:{scan_f[3]:02}"

            antennas = [str(a['nosta']) +  '-' + a['anname'].strip() for a in uvdata.table('AN', 1) 
                        if a['nosta'] in calibrator_scans[0].calib_antennas[:-1]]
            antennas = list(dict.fromkeys(antennas)) # Remove duplicates
            flagged_antennas = [str(a['nosta']) +  '-' + a['anname'].strip() for a in uvdata.table('AN', 1) 
                        if a['nosta'] in no_calib_antennas]
            flagged_antennas = list(dict.fromkeys(flagged_antennas)) # Remove duplicates
            
            print(f"\n{'Source:':<12} {calibrator_scans[0].source_name}")
            print(f"\n{'Time:':<12} {init_str} - {fin_str}")
            print(f"\n{'Antennas:':<12} {antennas}")
            print(f"\n{'Mean SNR:':<12} {calibrator_scans[0].calib_snr}\n")
            if len(no_calib_antennas) > 0:
                print(f"\nThere were no fringes with SNR > 5 to antennas: {flagged_antennas},\n")
                print(f"They will be flagged.\n\n")
                print('FG#3 created.\n')
            print('\nSN#1 created.\n')

        else:
            print('\nThe chosen scans for calibration are:\n')
            for scn in calibrator_scans:
                scan_i = help.ddhhmmss(scn.time - scn.time_interval / 2)
                scan_f = help.ddhhmmss(scn.time + scn.time_interval / 2)
                init_str = f"{scan_i[0]:02}/{scan_i[1]:02}:{scan_i[2]:02}:{scan_i[3]:02}"
                fin_str  = f"{scan_f[0]:02}/{scan_f[1]:02}:{scan_f[2]:02}:{scan_f[3]:02}"

                antennas = [str(a['nosta']) +  '-' + a['anname'].strip() for a in uvdata.table('AN', 1) 
                            if a['nosta'] in scn.calib_antennas[:-1]]
                antennas = list(dict.fromkeys(antennas)) # Remove duplicates
                flagged_antennas = [str(a['nosta']) +  '-' + a['anname'].strip() for a in uvdata.table('AN', 1) 
                            if a['nosta'] in no_calib_antennas]
                flagged_antennas = list(dict.fromkeys(flagged_antennas)) # Remove duplicates

                print(f"\n{'Source:':<12} {scn.source_name}")
                print(f"\n{'Time:':<12} {init_str} - {fin_str}")
                print(f"\n{'Antennas:':<12} {antennas}")
                print(f"\n{'Mean SNR:':<12} {scn.calib_snr}\n")

            if len(no_calib_antennas) > 0:
                print(f"\nThere were no fringes with SNR > 5 to antennas: {flagged_antennas},\n")
                print(f"They will be flagged.\n\n")
                print('FG#3 created.\n')
            print('\nSN#1 created.\n')

        print('Execution time: {:.2f} s. \n'.format(t7-t6))
        try:
            scan_dict = \
                {scan.time: (scan.source_name, inst.ddhhmmss(scan.time).tolist(), [sum(inner) / len(inner) for inner in scan.snr], scan.antennas) for scan in scan_list}
            calibscans_dict = \
                {scan.time: (scan.source_name, inst.ddhhmmss(scan.time).tolist(), [sum(inner) / len(inner) for inner in scan.snr], scan.calib_antennas) for scan in calibrator_scans}
        except TypeError: # Single IF
            scan_dict = \
                {scan.time: (scan.source_name, inst.ddhhmmss(scan.time).tolist(), scan.snr, scan.antennas) for scan in scan_list}
            calibscans_dict = \
                {scan.time: (scan.source_name, inst.ddhhmmss(scan.time).tolist(), scan.snr, scan.calib_antennas) for scan in calibrator_scans}

        stats_df['SNR_scan_list'] = json.dumps(scan_dict)
        stats_df['selected_scans'] = json.dumps(calibscans_dict)
        if len(no_calib_antennas) > 0:
            stats_df['antennas_no_calib'] = str(no_calib_antennas)
        else:
            stats_df['antennas_no_calib'] = False
        stats_df['calibrator_search'] = 'AUTO'
        stats_df['time_10'] = t7 - t6
        
    # If there is an input calibrator
    if input_calibrator != None:
        ## Look for calibrator ##
        ## SNR fringe search ##
        disp.write_box(log_list, 'Calibrator search')
        disp.print_box('Calibrator search')
        
        #snr_fring(uvdata, refant)
        cali.snr_fring(uvdata, refant, priority_refants)
        
        ## Get a list of scans ordered by SNR ##
        
        scan_list = cali.snr_scan_list_v2(uvdata)
        
        ## Get the scans for the input calibrator ## 
        calibrator_scans = [x for x in scan_list if x.source_name == input_calibrator]
        ## Order by SNR
        calibrator_scans.sort(key=lambda x: np.nanmedian(x.snr),\
                   reverse=True)
        
        calibrator_scans = [calibrator_scans[0]]
        t7 = time.time()

        for pipeline_log in log_list:
            pipeline_log.write('\nThe chosen scan for calibration is:\n')
            pipeline_log.write(str(calibrator_scans[0].source_name) + '\t\tSNR: ' \
                                + '{:.2f}.'.format(np.nanmedian(calibrator_scans[0].snr)))
            pipeline_log.write('\nSN#1 created.\n')
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t7-t6))

        print('\nThe chosen scan for calibration is:\n')
        print(str(calibrator_scans[0].source_name) + '\tSNR: ' \
                        + '{:.2f}.'.format(np.nanmedian(calibrator_scans[0].snr)))
        print('\nSN#1 created.\n')
        print('Execution time: {:.2f} s. \n'.format(t7-t6))

        scan_dict = \
            {scan.time: (scan.source_name, inst.ddhhmmss(scan.time).tolist(), np.nanmedian(scan.snr), scan.antennas) for scan in scan_list}
        calibscans_dict = \
            {scan.time: (scan.source_name, inst.ddhhmmss(scan.time).tolist(), np.nanmedian(scan.snr), scan.calib_antennas) for scan in calibrator_scans}

        stats_df['SNR_scan_list'] = json.dumps(scan_dict)
        stats_df['selected_scans'] = json.dumps(calibscans_dict)
        stats_df['antennas_no_calib'] = 'MANUAL'
        stats_df['calibrator_search'] = 'MANUAL'
        stats_df['time_10'] = t7 - t6

    # Counting again the visibilities with the flags
    expo.data_split(uvdata, target_list, cl_table=4, flagver=3, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl4_fg3 = AIPSUVData(target, 'PLOT', uvdata.disk, 4)
        vis_cl4_fg3, vis_ant_cl4_fg3 = expo.vis_count_v2(cl4_fg3)
        stats_df.at[i, 'CL4_vis_FG3'] = int(vis_cl4_fg3)
        stats_df.at[i, 'CL4_FG3_ant_vis'] = json.dumps(vis_ant_cl4_fg3)
        print(f"CL4 visibilities of {target} after flagging: {vis_cl4_fg3}{disp.vis_frac(vis_cl4_fg3, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL4 visibilities of {target} after flagging: {vis_cl4_fg3}{disp.vis_frac(vis_cl4_fg3, stats_df.at[i, 'CL1_vis'])}\n")

    ## Digital sampling correction ##
    disp.write_box(log_list, 'Digital sampling corrections')
    disp.print_box('Digital sampling corrections')
    
    accr.sampling_correct(uvdata)

    for pipeline_log in log_list:
        pipeline_log.write('\nDigital sampling corrections applied!\nSN#2 and CL#5'\
                        + ' created.\n')
    print('\nDigital sampling corrections applied!\nSN#2 and CL#5 created.\n')

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=5, flagver=3, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl5 = AIPSUVData(target, 'PLOT', uvdata.disk, 5)
        vis_cl5, vis_ant_cl5 = expo.vis_count_v2(cl5)
        stats_df.at[i, 'CL5_vis'] = int(vis_cl5)
        stats_df.at[i, 'CL5_ant_vis'] = json.dumps(vis_ant_cl5)
        print(f"CL5 visibilities of {target}: {vis_cl5}{disp.vis_frac(vis_cl5, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL5 visibilities of {target}: {vis_cl5}{disp.vis_frac(vis_cl5, stats_df.at[i, 'CL1_vis'])}\n")

    t8 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t8-t7))
    print('Execution time: {:.2f} s. \n'.format(t8-t7))

    stats_df['time_11'] = t8 - t7

    ## Instrumental phase correction ##
    disp.write_box(log_list, 'Instrumental phase corrections')
    disp.print_box('Instrumental phase corrections')
    
    inst.manual_phasecal_multi(uvdata, refant, priority_refants, calibrator_scans)
    
    for pipeline_log in log_list:
        pipeline_log.write('\nInstrumental phase correction applied using'\
                        + ' the calibrator(s).\nSN#3 and CL#6 created.\n')
    print('\nInstrumental phase correction applied using the calibrator(s).'\
          + '\nSN#3 and CL#6 created.\n')
    
    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=6, flagver=3, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl6 = AIPSUVData(target, 'PLOT', uvdata.disk, 6)
        vis_cl6, vis_ant_cl6 = expo.vis_count_v2(cl6)
        stats_df.at[i, 'CL6_vis'] = int(vis_cl6)
        stats_df.at[i, 'CL6_ant_vis'] = json.dumps(vis_ant_cl6)
        print(f"CL6 visibilities of {target}: {vis_cl6}{disp.vis_frac(vis_cl6, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL6 visibilities of {target}: {vis_cl6}{disp.vis_frac(vis_cl6, stats_df.at[i, 'CL1_vis'])}\n")

    t9 = time.time()
    
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t9-t8))
    print('Execution time: {:.2f} s. \n'.format(t9-t8))


    stats_df['time_12'] = t9 - t8

    ## Bandpass correction ##
    disp.write_box(log_list, 'Bandpass correction')
    disp.print_box('Bandpass correction')
    
    bpas.bp_correction(uvdata, refant, calibrator_scans)

    t10 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nBandpass correction applied!\nBP#1 created.\n')
    print('\nBandpass correction applied!\nBP#1 created.\n')

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=6, flagver=3, bpass = True, \
                    keep = True, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl6_bp1 = AIPSUVData(target, 'PLOTBP', uvdata.disk, 6)
        vis_cl6_bp1, vis_ant_cl6_bp1 = expo.vis_count_v2(cl6_bp1)
        stats_df.at[i, 'CL6_BP1_vis'] = int(vis_cl6_bp1)
        stats_df.at[i, 'CL6_BP1_ant_vis'] = json.dumps(vis_ant_cl6_bp1)
        print(f"CL6 + BP1 visibilities of {target}: {vis_cl6_bp1}{disp.vis_frac(vis_cl6_bp1, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL6 + BP1 visibilities of {target}: {vis_cl6_bp1}{disp.vis_frac(vis_cl6_bp1, stats_df.at[i, 'CL1_vis'])}\n")

    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t10-t9))
    print('Execution time: {:.2f} s. \n'.format(t10-t9))

    stats_df['time_13'] = t10 - t9


    ## Correcting autocorrelations ##
    disp.write_box(log_list, 'Correcting autocorrelations')
    disp.print_box('Correcting autocorrelations')

    accr.autocorr_correct(uvdata)


    for pipeline_log in log_list:
        pipeline_log.write('\nAutocorrelations have been normalized!\nSN#4 and CL#7'\
                        + ' created.\n')
    print('\nAutocorrelations have been normalized!\nSN#4 and CL#7 created.\n')

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=7, flagver=3, bpass = True, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl7_bp1 = AIPSUVData(target, 'PLOTBP', uvdata.disk, 7)
        vis_cl7_bp1, vis_ant_cl7_bp1 = expo.vis_count_v2(cl7_bp1)
        stats_df.at[i, 'CL7_BP1_vis'] = int(vis_cl7_bp1)
        stats_df.at[i, 'CL7_BP1_ant_vis'] = json.dumps(vis_ant_cl7_bp1)
        print(f"CL7 + BP1 visibilities of {target}: {vis_cl7_bp1}{disp.vis_frac(vis_cl7_bp1, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL7 + BP1 visibilities of {target}: {vis_cl7_bp1}{disp.vis_frac(vis_cl7_bp1, stats_df.at[i, 'CL1_vis'])}\n")

    t11 = time.time()
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t11-t10))
    print('Execution time: {:.2f} s. \n'.format(t11-t10))

    stats_df['time_14'] = t11 - t10


    ## Amplitude calibration ##
    disp.write_box(log_list, 'Amplitude calibration')
    disp.print_box('Amplitude calibration')
    
    ampc.amp_cal(uvdata)

    for pipeline_log in log_list:
        pipeline_log.write('\nAmplitude calibration applied!\nSN#5 and CL#8'\
                        + ' created.\n')
    print('\nAmplitude calibration applied!\nSN#5 and CL#8 created.\n')

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=8, flagver=3, bpass = True, flag_frac = flag_edge)
    for i, target in enumerate(target_list):
        cl8_bp1 = AIPSUVData(target, 'PLOTBP', uvdata.disk, 8)
        vis_cl8_bp1, vis_ant_cl8_bp1 = expo.vis_count_v2(cl8_bp1)
        stats_df.at[i, 'CL8_BP1_vis'] = int(vis_cl8_bp1)
        stats_df.at[i, 'CL8_BP1_ant_vis'] = json.dumps(vis_ant_cl8_bp1)
        print(f"CL8 + BP1 visibilities of {target}: {vis_cl8_bp1}{disp.vis_frac(vis_cl8_bp1, stats_df.at[i, 'CL1_vis'])}\n")
        log_list[i].write(f"\nCL8 + BP1 visibilities of {target}: {vis_cl8_bp1}{disp.vis_frac(vis_cl8_bp1, stats_df.at[i, 'CL1_vis'])}\n")

    t12 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s.\n'.format(t12-t11))
    print('Execution time: {:.2f} s.\n'.format(t12-t11))

    stats_df['time_15'] = t12 - t11
    
    ## Get optimal solution interval for each target
    disp.write_box(log_list, 'Target fringe fit')
    disp.print_box('Target fringe fit')

    # If there are no phase reference sources, make the length of the list match the 
    # target list length
    if phase_ref == None:
        phase_ref = [None] * len(target_list)
    
    solint_list = []
    for i, target in enumerate(target_list):
        if phase_ref[i] == None:
            target_scans = [x for x in scan_list if x.source_name == target]

            if default_solint == None:

                solint, solint_dict = opti.optimize_solint_mm(uvdata, target, \
                                                        target_scans, refant, 
                                                        min_solint = min_solint,
                                                        max_solint = max_solint)
                
                solint_list.append(solint) 

                if solint_list[i] != 1:
                    log_list[i].write('\nThe optimal solution interval for the target is '\
                                + str(solint_list[i]) + ' minutes. \n')
                    print('\nThe optimal solution interval for ' + target + ' is ' \
                        + str(solint_list[i]) + ' minutes. \n')
                else:
                    log_list[i].write('\nThe optimal solution interval for the target is '\
                                + str(solint_list[i]) + ' minute. \n')
                    print('\nThe optimal solution interval for ' + target + ' is ' \
                        + str(solint_list[i]) + ' minute. \n')    

            else:
                solint = default_solint
                solint_list.append(solint) 
                solint_dict = {default_solint: 'MANUAL'}
                log_list[i].write('\nThe optimal solution interval has been manually selected as '\
                            + str(solint_list[i]) + ' minutes. \n')
                print('\nThe optimal solution interval has been manually selected as ' \
                    + str(solint_list[i]) + ' minute. \n')     

            stats_df.at[i, 'solint'] = solint_list[i]
            stats_df.at[i, 'solint_dict'] = json.dumps(solint_dict)        
        else:
            phase_ref_scans = [x for x in scan_list if x.source_name == phase_ref[i]]

            if default_solint == None:

                solint, solint_dict = opti.optimize_solint_mm(uvdata, phase_ref[i], \
                                                        phase_ref_scans, refant, 
                                                        min_solint = min_solint,
                                                        max_solint = max_solint)
                
                solint_list.append(solint)

                if solint_list[i] != 1:
                    log_list[i].write('\nThe optimal solution interval for the phase ' \
                                    + 'calibrator ' + phase_ref[i] + ' is ' + str(solint_list[i]) + ' minutes. \n')
                    print('\nThe optimal solution interval for the phase calibrator ' + phase_ref[i] + ' is ' \
                        + str(solint_list[i]) + ' minutes. \n')
                else:
                    log_list[i].write('\nThe optimal solution interval for the phase ' \
                                    + 'calibrator ' + phase_ref[i] + ' is ' + str(solint_list[i]) + ' minute. \n')
                    print('\nThe optimal solution interval for the phase calibrator ' + phase_ref[i] + ' is ' \
                        + str(solint_list[i]) + ' minute. \n') 

            else:
                solint = default_solint
                solint_list.append(solint) 
                solint_dict = {default_solint: 'MANUAL'}
                log_list[i].write('\nThe optimal solution interval has been manually selected as '\
                            + str(solint_list[i]) + ' minutes. \n')
                print('\nThe optimal solution interval has been manually selected as ' \
                    + str(solint_list[i]) + ' minute. \n')  

            stats_df.at[i, 'solint'] = solint_list[i]
            stats_df.at[i, 'solint_dict'] = json.dumps(solint_dict)   
                          
    t13 = time.time()
    
    for pipeline_log in log_list:    
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t13-t12)) 
    print('Execution time: {:.2f} s. \n'.format(t13-t12))

    stats_df['time_16'] = t13-t12

    ## Fringe fit of the target ##

    ignore_list = []

    # Separate in no phaseref and phaseref targets
    ff_target_list = []
    for i, target in enumerate(target_list):
        t = help.FFTarget()
        t.name = target
        t.phaseref = phase_ref[i]
        t.solint = solint_list[i]
        t.log = log_list[i]
        ff_target_list.append(t)

    no_pr_target_list = [t for t in ff_target_list if t.phaseref is None]
    pr_target_list = [t for t in ff_target_list if t.phaseref is not None]

    ## NO PHASEREF FRINGE FIT ##
    for i, target in enumerate(no_pr_target_list):
        r = stats_df.index[stats_df['target'] == target.name][0]
        stats_df.at[r, 'phaseref_ff'] = False

        ratio, ratio_single, stats = frng.fringe_fit_with_fallback(
            uvdata, refant, priority_refants, fringefit_snr,
            target.name, target, version=6 + i, flag_edge=flag_edge)

        if ratio + ratio_single == 0:
            ignore_list.append(target.name)
        for key, value in stats.items():
            stats_df.at[r, key] = value

    ## PHASEREF FRINGE FIT ##
    pr_sn = uvdata.table_highver('SN') + 1

    for i, target in enumerate(pr_target_list):
        r = stats_df.index[stats_df['target'] == target.name][0]
        stats_df.at[r, 'phaseref_ff'] = False

        ratio, ratio_single, stats = frng.fringe_fit_with_fallback(
            uvdata, refant, priority_refants, fringefit_snr,
            target.phaseref, target, version=pr_sn + i,
            label='the phase calibrator: ', flag_edge=flag_edge)

        if ratio + ratio_single == 0:
            ignore_list.append(target.name)
        for key, value in stats.items():
            stats_df.at[r, key] = value

    # Apply all SN tables into CL9
    no_pr_names = [t.name for t in no_pr_target_list]
    no_pr_target_scans = [x for x in scan_list if x.source_name in no_pr_names]
    if len(no_pr_target_list) > 0:
        frng.fringe_clcal(uvdata, refant, no_pr_target_list, no_pr_target_scans,
                          max_ver=pr_sn - 1)
    else:
        # Create a CL9 if it has not been created before
        help.tacop(uvdata, 'CL', 8, 9)
    frng.fringe_phaseref_clcal(uvdata, refant, pr_target_list, version=pr_sn)

    t14 = time.time()
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t14 - t13))
    print('Execution time: {:.2f} s. \n'.format(t14 - t13))

    stats_df['time_17'] = t14 - t13

    ##  Export data ##
    t_export = time.time()
    disp.write_box(log_list, 'Exporting visibility data')
    disp.print_box('Exporting visibility data')

    no_baseline = expo.data_export(outpath_list, uvdata, target_list, \
                                   filename_list, ignore_list, channel_out,\
                                   flag_frac = flag_edge)
    

    for i, target in enumerate(target_list): 
        if target in ignore_list:
            stats_df.at[i, 'exported_size'] = 0
            continue
        if target not in no_baseline:
            log_list[i].write('\n' + target + ' visibilites exported to ' \
                              + outpath_list[i] + '/' + filename_list[i]  + '.uvfits\n')
            print('\n' + target + ' visibilites exported to ' \
                              + outpath_list[i] + '/' + filename_list[i]  + '.uvfits\n')
            
            stats_df.at[i, 'exported_size_mb'] = \
                os.path.getsize(outpath_list[i] + '/' + filename_list[i] + '.uvfits')/1024**2

        else:
            stats_df.at[i, 'exported_size'] = 0
            log_list[i].write('\n' + target + ' visibilites could not be exported, ' \
                              + 'there are not enough solutions to form a baseline.\n')
            print('\n' + target + ' visibilites could not be exported, ' \
                              + 'there are not enough solutions to form a baseline.\n')
                     

    expo.table_export(outpath_list, uvdata, target_list, filename_list)
    for i, target in enumerate(target_list): 
        log_list[i].write('\n' + target + ' calibration tables exported to '
                          + outpath_list[i] + '/TABLES/' \
                          + filename_list[i] + '.caltab.uvfits\n')
        print('\n' + target + ' calibration tables exported to '
                          + outpath_list[i] + '/TABLES/' \
                          + filename_list[i] + '.caltab.uvfits\n')
        
    # Counting visibilities
    expo.data_split(uvdata, [t for t in target_list if t not in ignore_list and t not in no_baseline], \
                    cl_table=9, flagver=3, bpass = True, flag_frac = flag_edge)
    
    for i, target in enumerate(target_list):
        r =  stats_df.index[stats_df['target'] == target][0]
        if target not in ignore_list and target not in no_baseline:
            cl9_bp1 = AIPSUVData(target, 'PLOTBP', uvdata.disk, 9)
            vis_cl9_bp1, vis_ant_cl9_bp1 = expo.vis_count_v2(cl9_bp1)
            stats_df.at[r, 'CL9_BP1_vis'] = int(vis_cl9_bp1)
            stats_df.at[i, 'CL9_BP1_ant_vis'] = json.dumps(vis_ant_cl9_bp1)
            print(f"CL9 + BP1 visibilities of {target}: {vis_cl9_bp1}{disp.vis_frac(vis_cl9_bp1, stats_df.at[i, 'CL1_vis'])}\n")
            log_list[i].write(f"\nCL9 + BP1 visibilities of {target}: {vis_cl9_bp1}{disp.vis_frac(vis_cl9_bp1, stats_df.at[i, 'CL1_vis'])}\n")
        else:
            stats_df.at[r, 'CL9_BP1_vis'] = 0
            antenna_names = [x.anname.strip() for x in uvdata.table('AN', 1)]
            vis_ant_cl9_bp1 = dict(zip(antenna_names, [0]*len(antenna_names)))
            stats_df.at[i, 'CL9_BP1_ant_vis'] = json.dumps(vis_ant_cl9_bp1)
        
    stats_df['time_18'] = time.time() - t_export

    ## PLOTS ##

    ######################## PLOTS FOR THE GUI ########################
    t_interactive = time.time()

    if interactive ==  True:
        disp.print_box("Generating interactive plots")
        disp.write_box(log_list, "Generating interactive plots")
        plot.generate_pickle_plots(uvdata, target_list, outpath_list)

        for i, path in enumerate(outpath_list):
            target_name = path.split('/')[-1]
            plot_size = sum(
                f.stat().st_size for f in Path(tmp_dir).rglob('*')
                if f.is_file() and target_name in f.name)
            
            stats_df.at[i, 'int_plot_size_mb'] = plot_size / 1024**2
            log_list[i].write(f'\nSize of generated interactive plots for {target_list[i]}: {round(plot_size / 1024**2, 2)} Mb\n')
        for pipeline_log in log_list:    
            pipeline_log.write('\nExecution time: {:.2f} s.\n'.format(time.time()-t_interactive))
        
        print(f'Total interactive plot files size: {round(stats_df["int_plot_size_mb"].sum(), 2)} Mb.')
        print('\nExecution time: {:.2f} s.\n'.format(time.time()-t_interactive))
    
    else:
        for i, path in enumerate(outpath_list):
            stats_df.at[i, 'int_plot_size_mb'] = 0

    stats_df['time_19'] = time.time() - t_interactive

    ###################################################################

    t_plots = time.time()

    ## Plot visibilities as a function of frequency of target and calibrator ## 
    disp.write_box(log_list, 'Plotting visibilities')
    disp.print_box('Plotting visibilities')
    
    ## Uncalibrated ##
    for i, target in enumerate(target_list):
            try:
                plot.possm_plotter(outpath_list[i], uvdata, target, 
                                            gainuse = 1, bpver = 0, \
                                            flagver=1, flag_edge=flag_edge)
                log_list[i].write('\nUncalibrated visibilities plotted in '
                                + outpath_list[i] + '/PLOTS/'  \
                                + filename_list[i] + '_CL1_POSSM.pdf\n')
                print('\nUncalibrated visibilities plotted in '
                                + outpath_list[i] + '/PLOTS/'  \
                                + filename_list[i] + '_CL1_POSSM.pdf\n')
                
            except RuntimeError:
                log_list[i].write('\nUncalibrated visibilities could not be plotted\n')
                print('\nUncalibrated visibilities could not be plotted\n')

        
    ## Calibrated ##
    for i, target in enumerate(target_list):
        if target in ignore_list:
            continue
        if target not in no_baseline:    
            try: 
                plot.possm_plotter(outpath_list[i], uvdata, target, 
                                            gainuse = 9, bpver = 1, 
                                            flag_edge=flag_edge)
                log_list[i].write('Calibrated visibilities plotted in '
                                + outpath_list[i] + '/PLOTS/' \
                                + filename_list[i] + '_CL' + str(9) + '_POSSM.pdf\n')
                print('Calibrated visibilities plotted in '
                                + outpath_list[i] + '/PLOTS/' \
                                + filename_list[i] + '_CL' + str(9) + '_POSSM.pdf\n')
            except RuntimeError:
                log_list[i].write('\nCalibrated visibilities could not be plotted\n')
                print('\nCalibrated visibilities could not be plotted\n')

        
    ## Plot uv coverage ##
    for i, target in enumerate(target_list):
        if target in ignore_list:
            continue
        if target not in no_baseline:
            try:
                plot.uvplt_plotter(outpath_list[i], uvdata, target)
                log_list[i].write('UV coverage plotted in '
                                + outpath_list[i] + '/PLOTS/' \
                                + filename_list[i] + '_UVPLT.pdf\n')
                print('UV coverage plotted in '
                                + outpath_list[i] + '/PLOTS/' \
                                + filename_list[i] + '_UVPLT.pdf\n')
            except RuntimeError:
                log_list[i].write('UV coverage could not be plotted\n')
                print('UV coverage could not be plotted\n')    

        
    ## Plot visibilities as a function of time of target ## 
    for i, target in enumerate(target_list):
        if target in ignore_list:
            continue
        if target not in no_baseline:
            try:
                plot.vplot_plotter(outpath_list[i], uvdata, target, 9, bpver = 1,
                                   flag_edge=flag_edge)
                log_list[i].write('Visibilities as a function of time plotted in '
                                + outpath_list[i] + '/PLOTS/' \
                                + filename_list[i]  + '_VPLOT.pdf\n')
                print('Visibilities as a function of time plotted in '
                                + outpath_list[i] + '/PLOTS/' \
                                + filename_list[i]  + '_VPLOT.pdf\n')
            except RuntimeError:
                log_list[i].write('Visibilities as a function of time could not be ' \
                                  + 'plotted\n')
                print('Visibilities as a function of time could not be plotted\n')
                
    ## Plot visibilities as a function of uv distance of target ##
    if interactive == False:
        #plot.generate_pickle_radplot(uvdata, [t for t in  target_list \
        #        if t not in ignore_list and t not in no_baseline], outpath_list)
        plot.generate_pickle_radplot(uvdata, target_list, outpath_list)

    for i, target in enumerate(target_list):
        if target not in ignore_list and target not in no_baseline:
            target_name = outpath_list[i].split('/')[-1]
            fig = pickle.load(open(f'{tmp_dir}/{target_name}.radplot.pickle', 'rb'))
            # Keep the color scheme in black and white, for consistency with other plots
            for ax in fig.get_axes():
                for line in ax.get_lines():
                    line.set_color('black')
                for text in ax.texts:
                    text.set_color('black')
                for spine in ax.spines.values():
                    spine.set_color('black')
                ax.title.set_color('black')
                ax.xaxis.label.set_color('black')
                ax.yaxis.label.set_color('black')
                ax.tick_params(colors='black')
                for collection in ax.collections:
                    collection.set_edgecolor('black')
                    collection.set_facecolor('black')

            # Set rasterization on individual elements
            for ax in fig.get_axes():
                for coll in ax.collections:
                    coll.set_rasterized(True)
                for line in ax.lines:
                    line.set_rasterized(True)

            fig.tight_layout()
            fig.savefig(f'{outpath_list[i]}/PLOTS/{filename_list[i]}_RADPLOT.pdf',
                bbox_inches='tight', dpi=330, format='pdf')

            log_list[i].write('Visibilities as a function of uv-distance plotted in '
                              + outpath_list[i] + '/PLOTS/' \
                              + filename_list[i]  + '_RADPLOT.pdf\n')
            print('Visibilities as a function of uv-distance plotted in '
                              + outpath_list[i] + '/PLOTS/' \
                              + filename_list[i]  + '_RADPLOT.pdf\n')    
            
    ## Plot visibilities per antenna across the calibration
    plot.plot_vis_per_antenna(stats_df, target_list, filename_list, outpath_list)

    for i, target in enumerate(target_list):
        log_list[i].write('Visibility timeline per antenna plotted in '
                        + outpath_list[i] + '/PLOTS/' \
                        + filename_list[i]  + '_VISANT.pdf\n')
        print('Visibility timeline per antenna plotted in '
                        + outpath_list[i] + '/PLOTS/' \
                        + filename_list[i]  + '_VISANT.pdf\n')


    for i, target in enumerate(target_list):
        plot_size = sum(f.stat().st_size for f in Path(outpath_list[i] + '/PLOTS/').rglob('*') if f.is_file())
        stats_df.at[i, 'plot_size_mb'] = plot_size / 1024**2

    t15 = time.time()
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s.\n'.format(t15-t14))
    print('Execution time: {:.2f} s.\n'.format(t15-t14))

    stats_df['time_20'] = t15 - t_plots

    ## Total execution time ##
    tf = time.time()
    for pipeline_log  in log_list:
        pipeline_log.write('\nScript run time: '\
                         + '{:.2f} s.\n'.format(tf-t_i))
        pipeline_log.close()

    print('/'*88)
    print('/'*88 + '\n')

    print(f'Pipeline run has ended.\n')
    for i, target in enumerate(target_list):
        if stats_df.at[i, 'good_sols'] == False and stats_df.at[i, 'good_sols_single'] == False:
            print(f"\t{target}: Fringe fit failed for all possible solutions. Data were not exported.\n")

        elif stats_df.at[i, 'good_sols'] == False and stats_df.at[i, 'good_sols_single'] != False:
            print(f'\t{target}: Fringe fit successful for '
                  + f"{int(stats_df.at[i, 'good_sols_single'])} out of "
                  + f"{int(stats_df.at[i, 'total_sols_single'])} possible solutions.\n")
            if target in no_baseline:
                print(f"\tThere were not enough solutions to form a baseline. Data were not exported.\n")
            else:
                print(f"\tData were exported to {outpath_list[i]}/{filename_list[i]}.uvfits")

            
        elif stats_df.at[i, 'good_sols'] != False and stats_df.at[i, 'good_sols_single'] == False:
            print(f'\t{target}: Fringe fit successful for '
                  + f"{int(stats_df.at[i, 'good_sols'])} out of "
                  + f"{int(stats_df.at[i, 'total_sols'])} possible solutions.\n")
            if target in no_baseline:
                print(f"\tThere were not enough solutions to form a baseline. Data were not exported.\n")
            else:
                print(f"\tData were exported to {outpath_list[i]}/{filename_list[i]}.uvfits")

        elif stats_df.at[i, 'good_sols']/stats_df.at[i, 'total_sols'] >= stats_df.at[i, 'good_sols_single']/stats_df.at[i, 'total_sols_single']:
            print(f'\t{target}: Fringe fit successful for '
                  + f"{int(stats_df.at[i, 'good_sols'])} out of "
                  + f"{int(stats_df.at[i, 'total_sols'])} possible solutions.\n")
            if target in no_baseline:
                print(f"\tThere were not enough solutions to form a baseline. Data were not exported.\n")
            else:
                print(f"\tData were exported to {outpath_list[i]}/{filename_list[i]}.uvfits")


        elif stats_df.at[i, 'good_sols']/stats_df.at[i, 'total_sols'] < stats_df.at[i, 'good_sols_single']/stats_df.at[i, 'total_sols_single']:
            print(f'\t{target}: Fringe fit successful for '
                  + f"{int(stats_df.at[i, 'good_sols_single'])} out of "
                  + f"{int(stats_df.at[i, 'total_sols_single'])} possible solutions.\n")
            if target in no_baseline:
                print(f"\tThere were not enough solutions to form a baseline. Data were not exported.\n")
            else:
                print(f"\tData were exported to {outpath_list[i]}/{filename_list[i]}.uvfits")

    print('\nPipeline run time: {:.2f} s.\n'.format(tf-t_i))

    print('/'*88)
    print('/'*88 + '\n')

    ######################## PRINT STATS ########################

    stats_df['total_time'] = tf - t_i
    for i, path in enumerate(outpath_list):
        stats_df.transpose().to_csv(f'{path}/{filename_list[i]}.stats.csv')

    ######################## PRINT STATS ######################## 
     

def pipeline(input_dict):
    """Read the inputs, split multiple frequencies and calibrate the dataset

    :param input_dict: _description_
    :type input_dict: _type_
    """    
    # Read logo
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    ASCII_PATH = os.path.join(CURRENT_DIR, "..", "GUI" ,"ascii_logo_string.txt")
    ascii_logo = open(ASCII_PATH, 'r').read()

    # Read the input dictionary
    AIPS.userno = input_dict['userno']
    disk_number = input_dict['disk']
    filepath_list = input_dict['paths']
    target_list = input_dict['targets']
    if target_list == ['']:
        target_list = []
    output_directory = input_dict['output_directory']
    # Calibration options
    inp_cal = input_dict['calib']
    calib_all = input_dict['calib_all']
    phase_ref = input_dict['phase_ref']
    # Loading options
    load_all =  input_dict['load_all']
    load_antab = input_dict['load_tables']
    load_flags = input_dict['load_flags']
    #def_selfreq = input_dict['freq_sel']
    #subarray = input_dict['subarray']
    shifts = input_dict['shifts']
    time_aver = input_dict['time_aver']
    freq_aver = input_dict['freq_aver']
    # Reference antenna options
    def_refant = input_dict['refant']
    def_refant_list = input_dict['refant_list']
    search_central = input_dict['search_central']
    max_scan_refant_search = input_dict['max_scan_refant_search']
    # Fringe options
    fringefit_snr = input_dict['fringe_snr']
    def_solint = input_dict['solint']
    min_solint = input_dict['min_solint']
    max_solint = input_dict['max_solint']
    # Export options
    channel_out = input_dict['channel_out']
    flag_edge = input_dict['flag_edge']
    # Plotting options
    interactive = input_dict['interactive']


    ## Clean tmp directory ##
    os.system(f'rm {tmp_dir}/*')

    ## If calibrate all is selected => load all is also selected
    if calib_all == True:
        load_all = True
        

        ## Split the dataset in frequency bands, one pipeline run per band ##
    bands = load.get_bands(filepath_list)

    for band in bands:

        t_0 = time.time()

        ## Select files to work with
        filepath_list_ID = band['files']

        # Are my sources in this frequency ID?
        if band['multi_id'] == True:
            missingso = load.are_sources_in_id(filepath_list, band['id'], target_list)
            if missingso != []:
                print(f"The following sources are missing on this frequency id {band['id']}:\n{missingso}\n")
                print(f'It will be skipped.\n')
                continue

        ## Select sources to load ##
        full_source_list = load.get_source_list(filepath_list_ID, freq = band['freq'])

        # Create a new variable so that the different bands are independent
        if load_all:
            load_all_id = True
            sources = [x.name for x in full_source_list]
        else:
            load_all_id = False
            if full_source_list[0].band not in ['S', 'C', 'X', 'U', 'K', 'Ka']:
                load_all_id = True
                sources = [x.name for x in full_source_list]

            else:
                try:
                    calibs, load_all_id = load.find_calibrators(full_source_list, choose='BYCOORD')
                    sources = calibs.copy()
                    sources += target_list
                    if phase_ref != None:
                        sources += [x for x in phase_ref if x is not None]
                except ValueError:
                    print("None of the sources was found on the VLBA calibrator list. All sources will be loaded.\n")
                    load_all_id = True
                    sources = [x.name for x in full_source_list]

        klass_1 = band['klass']

        # Define AIPS name
        date, obscode = load.get_date_obscode(filepath_list_ID)
        aips_name = obscode

        ## Check if the AIPS catalogue name is too long, and rename ##
        # 12 is the maximum length for a file name in AIPS
        aips_name_short = aips_name
        if len(aips_name) > 12:
            name = aips_name.split('_')[0]
            suffix = aips_name.split('_')[1]
            size_name = 12 - (len(suffix) + 1)
            aips_name_short = name[:size_name] + '_' + suffix

        # Check if project directory already exists, if not, create one
        project_dir = output_directory + '/' + obscode
        os.makedirs(project_dir, exist_ok = True)

        # If calibrate all is selected, every loaded source of this band is a target
        if calib_all == True:
            band_targets = sources.copy()
        else:
            band_targets = target_list.copy()

        ############################################
        ## KEEP TRACK OF ALL STATS IN A DATAFRAME ##
        ############################################
        stats_df = pd.DataFrame({"target": band_targets})
        stats_df['loaded_sources'] =  json.dumps(dict(zip(sources, [x.band_flux for x in full_source_list if x.name in sources])))
        stats_df['n_of_freqs'] = band['n_bands']

        # Create subdirectories for the targets and DELETE EXISTING ONES
        # Also, create the pipeline log file of each target
        filename_list = band_targets.copy()
        log_list = band_targets.copy()
        outpath_list = band_targets.copy()
        for i, name in enumerate(filename_list):
            filename_list[i] = name + '_' + obscode + '_' + klass_1 + '_' + date
            outpath_list[i] = project_dir + '/' + filename_list[i]
            if os.path.exists(outpath_list[i]) == True:
                shutil.rmtree(outpath_list[i])
            os.makedirs(outpath_list[i] + '/PLOTS')
            os.makedirs(outpath_list[i] + '/TABLES')
            log_list[i] = open(project_dir + '/' + filename_list[i] + '/' \
                            + filename_list[i] + '_VIPCALslog.txt', 'w+')
            log_list[i].write(ascii_logo + '\n')

        stats_df['t_0'] = time.time() - t_0

        ## START THE PIPELINE ##
        calibrate(filepath_list_ID, filename_list, outpath_list, log_list, band_targets,
          sources, load_all_id, full_source_list, disk_number, aips_name_short, klass_1,
          band['multi_id'], band['selfreq'], band['if_idx'], def_refant, def_refant_list, search_central,
          max_scan_refant_search, time_aver, freq_aver, fringefit_snr,
          def_solint, min_solint, max_solint, phase_ref,
          inp_cal, shifts, load_antab, load_flags, channel_out, flag_edge, interactive,
          stats_df)