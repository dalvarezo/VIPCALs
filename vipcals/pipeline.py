import os
import time 
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

from AIPS import AIPS

from astropy.coordinates import SkyCoord
from astropy.io import fits

import scripts.load_data as load
import scripts.display as disp
import scripts.load_tables as tabl
import scripts.ty_smooth as tysm
import scripts.refant_choose as rant
import scripts.ionos_corr as iono
import scripts.eop_corr as eopc
import scripts.accor as accr
import scripts.amp_cal as ampc
import scripts.pang_corr as pang
import scripts.calib_choose as cali
import scripts.instr_calib as inst
import scripts.plotter as plot
import scripts.bandpass as bpas
import scripts.fringe_fit as frng
import scripts.optimize_solint as opti
import scripts.export_data as expo
import scripts.phase_shift as shft

from AIPSData import AIPSUVData

import functools
print = functools.partial(print, flush=True)

def calibrate(filepath_list, aips_name, sources, full_source_list, target_list, \
             filename_list, log_list, path_list,\
             disk_number, klass = '', seq = 1, bif = 0, eif = 0, \
             multi_id = False, selfreq = 0, default_refant = 'NONE', \
             input_calibrator = 'NONE', load_all = False, shift_coords = 'None',
             flag_edge = 0, phase_ref = ['NONE'], stats_df = None):
    """Main workflow of the pipeline 

    :param filepath_list: list of paths to the original uvfits/idifits files
    :type filepath_list: list of str
    :param aips_name: name for the catalogue entry in AIPS
    :type aips_name: str
    :param sources: list with source names to be loaded
    :type sources: list of str
    :param full_source_list: list containing all sources in the dataset
    :type full_source_list: list of Source objects
    :param target_list: target names
    :type target_list: list of str
    :param filename_list: list containing the subdirectories of each target
    :type filename_list: list of str
    :param log_list: list of log files
    :type log_list: list of file
    :param path_list: list containing the file paths of each target
    :type path_list: list of str
    :param disk_number: disk number within AIPS
    :type disk_number: int
    :param klass: class name within AIPS; defaults to ‘’
    :type klass: str, optional
    :param seq: sequence number within AIPS; defaults to 1
    :type seq: int, optional
    :param bif: first IF to copy, 0 => 1; defaults to 0
    :type bif: int, optional
    :param eif: highest IF to copy, 0 => all higher than bif; defaults to 0
    :type eif: int, optional
    :param selfreq: if there are multiple frequency ids, which one to load; defaults to 0
    :type selfreq: int, optional
    :param default_refant: force the pipeline to choose this reference antenna by giving \
                           its antenna code; defaults to 'NONE'
    :type default_refant: str, optional
    :param input_calibrator: force the pipeline to use this source as calibrator; \
                             defaults to 'NONE'
    :type input_calibrator: str, optional
    :param load_all: load all sources on the dataset; default = False
    :type load_all: bool, optional
    :param shift_coords: list of new coordinates for the targets, as Astropy SkyCoord \
                         objects, in case a phase shift was necessary; defaults to 'NONE'
    :type shift_coords: list of SkyCoord
    :param flag_edge: fraction of the total channels to flag at the edge of each IF\
                        ; defaults to 0
    :type flag_edge: float, optional
    :param phase_ref: list of phase calibrator names for phase referencing; \
                      defaults to ['NONE']
    :type phase_ref: list of str, optional
    :param stats_df: Pandas DataFrame where to keep track of the different statistics
    :type stats_df: pandas.DataFrame object
    """    


    ## PIPELINE STARTS
    t_i = time.time()

    # AIPS log is registered simultaneously for all science targets
    load.open_log(path_list, filename_list)
        
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
    selfreq, klass = klass, bif = bif, eif = eif, l_a = load_all)
    load.write_info(uvdata, filepath_list, log_list, sources, stats_df=stats_df)
    t1 = time.time() 
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t1-t0))
    load.print_info(uvdata, filepath_list, sources)
    print('Execution time: {:.2f} s. \n'.format(t1-t0))
    stats_df['time_1'] = t1-t0

    ## Check data integrity
    print('\nChecking data integrity...\n')
    ## Modify the AN table in case there are non ASCII characters   
    try:
        uvdata.antennas
    except SystemError:
        tabl.remove_ascii_antname(uvdata, filepath_list[0])
        tabl.remove_ascii_poltype(uvdata)
        print('\nAN Table was modified to correct for padding in entries.\n')

    ## Check for order
    if uvdata.header['sortord'] != 'TB':
        tabl.tborder(uvdata, pipeline_log)
        for pipeline_log in log_list:
            pipeline_log.write('\nData was not in TB order. It has been reordered using '\
                               + 'the UVSRT task\n')
        print('\nData was not in TB order. It has been reordered using ' \
              + 'the UVSRT task\n')
        
        stats_df['need_uvsrt'] = 'Yes'
    else:
        stats_df['need_uvsrt'] = 'No'
    
    ## Check for CL/NX tables
    if [1, 'AIPS CL'] not in uvdata.tables or [1, 'AIPS NX'] not in \
        uvdata.tables:
        tabl.run_indxr(uvdata)
        print('\nINDXR was run, NX#1 and CL#1 were created.\n')
            
        stats_df['need_indxr'] = 'Yes'
    else:
        stats_df['need_indxr'] = 'No'

    ## Check for TY/GC/FG tables
    missing_tables = False
    stats_df['need_ty'] = 'No'
    stats_df['need_fg'] = 'No'
    stats_df['need_gc'] = 'No'
    stats_df['vlbacal_files'] = 'None'

    if ([1, 'AIPS TY'] not in uvdata.tables or [1, 'AIPS GC'] \
    not in uvdata.tables or [1, 'AIPS FG'] not in uvdata.tables):
        disp.write_box(log_list, 'Loading external table information')
        disp.print_box('Loading external table information')
        missing_tables = True
        t_i_table = time.time()

    if [1, 'AIPS TY'] not in uvdata.tables:
        retrieved_urls = tabl.load_ty_tables(uvdata, bif, eif)
        for pipeline_log in log_list:
            for good_url in retrieved_urls:
                pipeline_log.write('\nSystem temperatures were not available in the ' \
                                  + 'file, they have been retrieved from ' \
                                  + good_url + '\n')
            pipeline_log.write('TY#1 created.\n')

        # Move the temperature file to the target folders
        for path in path_list:
            os.system('cp ./tsys.vlba ' + path + '/TABLES/tsys.vlba')
    
        # And delete the files from the current directory
        os.system('rm ./tables*')
        os.system('rm ./tsys.vlba')
   
        print('\nSystem temperatures were not available in the ' \
                                  + 'file, they have been retrieved from \n' \
                                  + good_url + '\n')
        print('TY#1 created.\n')
        stats_df['need_ty'] = 'Yes'
        stats_df['vlbacal_files'] = retrieved_urls
        
    if [1, 'AIPS GC'] not in uvdata.tables:
        load_gc_tables_code = tabl.load_gc_tables(uvdata)
        good_url = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/vlba_gains.key'

        if load_gc_tables_code == 404:  # If no GC was found
            for pipeline_log in log_list:
                pipeline_log.write('WARNING: No gain curves were found at the '\
                                    + 'observed date. No GC table will be created.\n') 
            print('WARNING: No gain curves were found at the observed date. No ' \
              + 'GC table will be created.\n')
            
            return  # END THE PIPELINE!
        
        for pipeline_log in log_list:
            pipeline_log.write('\nGain curve information was not available in the '\
                               + 'file, it has been retrieved from\n' + good_url \
                               + '\nGC#1 created.\n\n')
            
        # Move the gain curve file to the target folders
        for path in path_list:
            os.system('cp ./gaincurves.vlba ' + path + '/TABLES/gaincurves.vlba')
    
        # And delete the files from the main directory
        os.system('rm ./gaincurves.vlba')           
        
        print('\nGain curve information was not available in the file, it has '\
          + 'been retrieved from\n' + good_url + '\nGC#1 created.\n')
        stats_df['need_gc'] = 'Yes'
        
        
    if [1, 'AIPS FG'] not in uvdata.tables:
        retrieved_urls = tabl.load_fg_tables(uvdata)
        for pipeline_log in log_list:
            for good_url in retrieved_urls:
                pipeline_log.write('Flag information was not available in the file, ' \
                                    + 'it has been retrieved from ' + good_url + '\n')
            pipeline_log.write('FG#1 created.\n')

        # Move the flag file to the target folders
        for path in path_list:
            os.system('cp ./flags.vlba ' + path + '/TABLES/flags.vlba')
    
        # And delete the files from the main directory
        os.system('rm ./tables*')
        os.system('rm ./flags.vlba')

        print('Flag information was not available in the file, ' \
                        + 'it has been retrieved from\n' + good_url + '\n')
        print('FG#1 created.\n')
        stats_df['need_fg'] = 'Yes'
        stats_df['vlbacal_files'] = retrieved_urls

    if missing_tables == True:
        t1 = time.time()
        for pipeline_log in log_list:
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t1-t_i_table))

    stats_df['time_2'] = time.time()-t1

    ## Shift phase center if necessary ##
    # No shift will be done if the new coordinates are 0h0m0s +0d0m0s, in that case the
    # source will not be altered

    
    if shift_coords != 'NONE':
        t_shift = time.time()
        disp.write_box(log_list, 'Shifting phase center')
        disp.print_box('Shifting phase center')
        for i, target in enumerate(target_list):
            if shift_coords[i] == SkyCoord(0, 0, unit = 'deg'):
                stats_df.at[i, 'uvshift'] = 'No'
                stats_df.at[i, 'time_3'] = 0
                old_coord = shft.get_coord(uvdata, target)
                stats_df.at[i, 'old_coords'] = old_coord.to_string(style = 'hmsdms')
                stats_df.at[i, 'new_coords'] = old_coord.to_string(style = 'hmsdms')
                continue
                
            stats_df.at[i, 'uvshift'] = 'Yes'
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
            
            ## Reorder data
            #tabl.tborder(uvdata, pipeline_log)
            ## Run indxr
            #uvdata.zap_table('CL', 1)
            #tabl.run_indxr(uvdata)
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
        stats_df['uvshift'] = 'No'
        for i, target in enumerate(target_list):
            old_coord = shft.get_coord(uvdata, target)
            stats_df.at[i, 'old_coords'] = old_coord.to_string(style = 'hmsdms')
            stats_df.at[i, 'new_coords'] = old_coord.to_string(style = 'hmsdms')

    # Update the sequence
    seq = uvdata.seq
    
    t_avg = time.time()
    ## If the time resolution is < 0.99s, average the dataset in time
    try:
        time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'][0])
    except TypeError: # Single IF datasets
        time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'])
        
    if time_resol < 0.99:
        avgdata = AIPSUVData(aips_name[:9] + '_AT', uvdata.klass, disk_number, seq)
        if avgdata.exists() == True:
            avgdata.zap()
        tabl.time_aver(uvdata, time_resol, 2)
        uvdata = AIPSUVData(aips_name[:9] + '_AT', uvdata.klass, disk_number, seq)

        # Index the data again
        uvdata.zap_table('CL', 1)
        tabl.run_indxr(uvdata)

        disp.write_box(log_list, 'Data averaging')
        disp.print_box('Data averaging')
        for pipeline_log in log_list:
            pipeline_log.write('\nThe time resolution was ' \
                            + '{:.2f}'.format(time_resol) \
                            + 's. It has been averaged to 2s.\n')
        print('\nThe time resolution was {:.2f}'.format(time_resol) \
            + 's. It has been averaged to 2s.\n')
        is_data_avg = True
        stats_df['time_avg'] = 'Yes'
        stats_df['old_timesamp'] = time_resol
        stats_df['new_timesamp'] = 2
    else:
        is_data_avg = False
        stats_df['time_avg'] = 'No'
        stats_df['old_timesamp'] = time_resol
        stats_df['new_timesamp'] = time_resol
        
            
    ## If the channel bandwidth is smaller than 0.5 MHz, average the dataset 
    ## in frequency up to 0.5 MHz per channel 
    try:
        ch_width = float(uvdata.table('CQ', 1)[0]['chan_bw'][0])
        no_chan = int(uvdata.table('CQ', 1)[0]['no_chan'][0])
    except TypeError: # Single IF datasets
        ch_width = float(uvdata.table('CQ', 1)[0]['chan_bw'])
        no_chan = int(uvdata.table('CQ', 1)[0]['no_chan'])
        
    if ch_width < 500000:
        if is_data_avg == False:
            avgdata = AIPSUVData(aips_name[:9] + '_AF', uvdata.klass, \
                                 disk_number, seq)
            if avgdata.exists() == True:
                avgdata.zap()
            f_ratio = 500000/ch_width    # NEED TO ADD A CHECK IN CASE THIS FAILS
            
            if time_resol >= 0.33: # => If it was not written before
                disp.write_box(log_list, 'Data averaging')
                disp.print_box('Data averaging')
            
            tabl.freq_aver(uvdata,f_ratio)
            uvdata = AIPSUVData(aips_name[:9] + '_AF', uvdata.klass, \
                                 disk_number, seq)

        if is_data_avg == True:
            avgdata = AIPSUVData(aips_name[:9] + '_ATF', uvdata.klass, \
                                 disk_number, seq)
            if avgdata.exists() == True:
                avgdata.zap()
            f_ratio = 500000/ch_width    # NEED TO ADD A CHECK IN CASE THIS FAILS
            
            tabl.freq_aver(uvdata,f_ratio)
            uvdata = AIPSUVData(aips_name[:9] + '_ATF', uvdata.klass, \
                                 disk_number, seq)

        # Index the data again
        uvdata.zap_table('CL', 1)
        tabl.run_indxr(uvdata)

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
              + '500 kHz.\n')
        
        stats_df['freq_avg'] = 'Yes'
        stats_df['old_ch_width'] = ch_width
        stats_df['old_ch_no'] = no_chan
        stats_df['new_ch_width'] = 500000
        stats_df['new_ch_no'] = no_chan_new
        
    else:
        stats_df['freq_avg'] = 'No'
        stats_df['old_ch_width'] = ch_width
        stats_df['old_ch_no'] = no_chan
        stats_df['new_ch_width'] = ch_width
        stats_df['new_ch_no'] = no_chan
        
    stats_df['time_4'] = time.time() - t_avg


    ## Print scan information ##    
    load.print_listr(uvdata, path_list, filename_list)
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
    expo.data_split(uvdata, target_list, cl_table=1, flagver=1)
    for i, target in enumerate(target_list):
        cl1 = AIPSUVData(target, 'PLOT', uvdata.disk, 1)
        vis_cl1 = expo.vis_count(cl1)
        stats_df.at[i, 'CL1_vis'] = int(vis_cl1)
        print(f"CL1 visibilities of {target}: {vis_cl1}\n")
    


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

            
    
    original_tsys, flagged_tsys, tsys_dict = tysm.ty_assess(uvdata)
    
    tsys_flag_percent = np.round(flagged_tsys/original_tsys*100, 2)

    for pipeline_log in log_list:
        pipeline_log.write("\nAntenna |  TY1  |  TY2 \n")
        pipeline_log.write("--------|-------|-------\n")
        for _, (ant, ty1, ty2) in tsys_dict.items():
            if ty1 != 0:
                pipeline_log.write(f"{ant.strip():<8}|  {ty1:<4} |  {ty2} \n")

        pipeline_log.write('\nSystem temperatures clipped: ' + str(tsys_flag_percent) \
                           + '% of the Tsys values have been flagged ('  \
                           + str(flagged_tsys) + '/' + str(original_tsys) + ')\n' \
                           + 'TY#2 created.\n')
        
    print("\nAntenna |  TY1  |  TY2 \n")
    print("--------|-------|-------\n")
    for _, (ant, ty1, ty2) in tsys_dict.items():
        if ty1 != 0:
            print(f"{ant.strip():<8}|  {ty1:<4} |  {ty2} \n")
     
    print('\nSystem temperatures clipped: ' + str(tsys_flag_percent) \
            + '% of the Tsys values have been flagged ('  \
            + str(flagged_tsys) + '/' + str(original_tsys) + ')\n' \
            + 'TY#2 created.\n') 
    
    t2 = time.time()  

    stats_df['ty1_points'] = original_tsys
    stats_df['ty2_points'] = original_tsys - flagged_tsys
    stats_df['tsys_dict'] = json.dumps(tsys_dict)

    # Remove unflagged splitted entries
    for i, target in enumerate(target_list):
        AIPSUVData(target, 'PLOT', uvdata.disk, 1).zap()

    # Counting again the visibilities with the flags
    expo.data_split(uvdata, target_list, cl_table=1, flagver=2)
    for i, target in enumerate(target_list):
        cl1_fg2 = AIPSUVData(target, 'PLOT', uvdata.disk, 1)
        vis_cl1_fg2 = expo.vis_count(cl1_fg2)
        stats_df.at[i, 'CL1_vis_FG2'] = int(vis_cl1)
        print(f"CL1 visibilities of {target} after flagging: {vis_cl1_fg2}\n")

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
    
    if default_refant == 'NONE':
        for pipeline_log in log_list:
            pipeline_log.write('\nCHOOSING REFANT WITH ALL SOURCES\n')

        refant, ant_dict = rant.refant_choose_snr(
            uvdata, sources, sources, target_list, full_source_list, log_list, load_all
        )

        refant_summary = (
            f"\n{ant_dict[refant].name} has been selected as the reference antenna "
            f"with an SNR of {round(ant_dict[refant].median_SNR, 2)}. It is available in "
            f"{len(ant_dict[refant].scans_obs)} out of {ant_dict[refant].max_scans} scans.\n"
        )

        for pipeline_log in log_list:
            pipeline_log.write(refant_summary)
            pipeline_log.write("Antenna  |   SNR   | Obs Scans | Tot Scans\n")
            pipeline_log.write("---------|---------|-----------|-----------\n")
            for ant in ant_dict.values():
                pipeline_log.write(
                    f"{ant.name:<8} | {round(ant.median_SNR,2):>6} |"
                    f" {len(ant.scans_obs):>9} | {ant.max_scans:>9}\n"
                )

        # Console output
        print(refant_summary)
        print("Antenna  |   SNR   | Obs Scans | Tot Scans")
        print("---------|---------|-----------|-----------")
        for ant in ant_dict.values():
            print(
                f"{ant.name:<8} | {round(ant.median_SNR,2):>6} |"
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
        stats_df['refant_rank'] = 'MANUAL'

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
        t4 = time.time()
        for pipeline_log in log_list:
            pipeline_log.write('\nIonospheric corrections applied!\nCL#2 created.'\
                            + '\n')
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t4-t3))
        print('\nIonospheric corrections applied!\nCL#2 created.\n')
        print('Execution time: {:.2f} s. \n'.format(t4-t3))
        os.system('rm -rf /tmp/jplg*')

        stats_df['iono_files'] = str(files)
        stats_df['time_7'] = t4 - t3

        # Counting visibilities
        expo.data_split(uvdata, target_list, cl_table=2, flagver=2)
        for i, target in enumerate(target_list):
            cl2 = AIPSUVData(target, 'PLOT', uvdata.disk, 2)
            vis_cl2 = expo.vis_count(cl2)
            stats_df.at[i, 'CL2_vis'] = int(vis_cl2)
            print(f"CL2 visibilities of {target}: {vis_cl2}\n")

    else:
        t4 = time.time()
        iono.tacop(uvdata, 'CL', 1, 2)
        for pipeline_log in log_list:
            pipeline_log.write('\nIonospheric corrections not applied! IONEX '\
                            + 'files are not available for observations '\
                            + 'older than June 1998.\nCL#2 will be copied '\
                            + 'from CL#1.\n')
        print('\nIonospheric corrections not applied! IONEX files are not '\
              + 'available for observations older than June 1998.\nCL#2 '\
              + 'will be copied from CL#1.\n')
        stats_df['iono_files'] = 'OLD'
        stats_df['time_7'] = t4 - t3

        # Counting visibilities
        expo.data_split(uvdata, target_list, cl_table=2, flagver=2)
        for i, target in enumerate(target_list):
            cl2 = AIPSUVData(target, 'PLOT', uvdata.disk, 2)
            vis_cl2 = expo.vis_count(cl2)
            stats_df.at[i, 'CL2_vis'] = int(vis_cl2)
            print(f"CL2 visibilities of {target}: {vis_cl2}\n")
        
    ## Earth orientation parameters correction ##
    disp.write_box(log_list, 'Earth orientation parameters corrections')
    disp.print_box('Earth orientation parameters corrections')

    eopc.eop_correct(uvdata)
    t5 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nEarth orientation parameter corrections applied!\n'\
                        + 'CL#3 created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t5-t4))
    print('\nEarth orientation parameter corrections applied!\nCL#3 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t5-t4))
    os.system('rm -rf /tmp/usno_finals.erp')

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=3, flagver=2)
    for i, target in enumerate(target_list):
        cl3 = AIPSUVData(target, 'PLOT', uvdata.disk, 3)
        vis_cl3 = expo.vis_count(cl3)
        stats_df.at[i, 'CL3_vis'] = int(vis_cl3)
        print(f"CL3 visibilities of {target}: {vis_cl3}\n")

    stats_df['time_8'] = t5 - t4

    ## Parallatic angle correction ##
    disp.write_box(log_list, 'Parallactic angle corrections')
    disp.print_box('Parallactic angle corrections')
    
    pang.pang_corr(uvdata)
    t6 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nParallactic angle corrections applied!\nCL#4'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t6-t5))
    print('\nParallactic angle corrections applied!\nCL#4 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t6-t5))

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=4, flagver=2)
    for i, target in enumerate(target_list):
        cl4 = AIPSUVData(target, 'PLOT', uvdata.disk, 4)
        vis_cl4 = expo.vis_count(cl4)
        stats_df.at[i, 'CL4_vis'] = int(vis_cl4)
        print(f"CL4 visibilities of {target}: {vis_cl4}\n")

    stats_df['time_9'] = t6 - t5

    ## Selecting calibrator scan ##
    # If there is no input calibrator
    if input_calibrator == 'NONE':
        ## Look for calibrator ##
        ## SNR fringe search ##
        disp.write_box(log_list, 'Calibrator search')
        disp.print_box('Calibrator search')
        
        #snr_fring(uvdata, refant)
        cali.snr_fring_only_fft(uvdata, refant)
        
        ## Get a list of scans ordered by SNR ##
        
        scan_list = cali.snr_scan_list_v2(uvdata)
        
        ## Check if snr_scan_list() returned an error and, if so, end the pipeline
        if scan_list == 404:
            for pipeline_log in log_list:
                pipeline_log.write('\nNone of the scans reached a minimum SNR of ' \
                                + '5 and the dataset could not be automatically ' \
                                + 'calibrated.\nThe pipeline will stop now.\n')
                
            print('\nNone of the scans reached a minimum SNR of ' \
                + '5 and the dataset could not be automatically ' \
                + 'calibrated.\nThe pipeline will stop now.\n')
                
            return()
        
        ## Get the calibrator scans
        calibrator_scans = cali.get_calib_scans(uvdata, scan_list, refant)

        t7 = time.time()

        for pipeline_log in log_list:
            if len(calibrator_scans) == 1:
                pipeline_log.write('\nThe chosen scan for calibration is:\n')
                pipeline_log.write(str(calibrator_scans[0].name) + '\tSNR: ' \
                                   + '{:.2f}.'.format(np.nanmedian(calibrator_scans[0].snr)))
                pipeline_log.write('\nSN#1 created.\n')

            else:
                pipeline_log.write('\nThe chosen scans for calibration are:\n')
                for scn in calibrator_scans:    
                    pipeline_log.write(str(scn.name) + '\tSNR: ' \
                                      + '{:.2f}.\n'.format(np.nanmedian(scn.snr)))
                pipeline_log.write('\nSN#1 created.\n')

            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t7-t6))

   
        if len(calibrator_scans) == 1:
            print('\nThe chosen scan for calibration is:\n')
            print(str(calibrator_scans[0].name) + '\tSNR: ' \
                            + '{:.2f}.'.format(np.nanmedian(calibrator_scans[0].snr)))
            print('\nSN#1 created.\n')

        else:
            print('\nThe chosen scans for calibration are:\n')
            for scn in calibrator_scans:    
                print(str(scn.name) + '\tSNR: {:.2f}.\n'.format(np.nanmedian(scn.snr)))
            print('\nSN#1 created.\n')

        print('Execution time: {:.2f} s. \n'.format(t7-t6))

        # Print a warning if the SNR of the brightest calibrator is < 40
        if np.nanmedian(calibrator_scans[0].snr) < 40:
            for pipeline_log in log_list:
                pipeline_log.write('\nWARNING: The brightest scan has a low SNR.\n')

            print('\nWARNING: The brightest scan has a low SNR.\n')

        scan_dict = \
            {scan.time: (scan.name, inst.ddhhmmss(scan.time).tolist(), np.nanmedian(scan.snr), scan.antennas) for scan in scan_list}
        calibscans_dict = \
            {scan.time: (scan.name, inst.ddhhmmss(scan.time).tolist(), np.nanmedian(scan.snr), scan.calib_antennas) for scan in calibrator_scans}

        stats_df['SNR_scan_list'] = json.dumps(scan_dict)
        stats_df['selected_scans'] = json.dumps(calibscans_dict)
        stats_df['calibrator_search'] = 'AUTO'
        stats_df['time_10'] = t7 - t6
        
    # If there is an input calibrator
    if input_calibrator != 'NONE':
        ## Look for calibrator ##
        ## SNR fringe search ##
        disp.write_box(log_list, 'Calibrator search')
        disp.print_box('Calibrator search')
        
        #snr_fring(uvdata, refant)
        cali.snr_fring_only_fft(uvdata, refant)
        
        
        ## Get a list of scans ordered by SNR ##
        
        scan_list = cali.snr_scan_list_v2(uvdata)
        
        ## Get the scans for the input calibrator ## 
        calibrator_scans = [x for x in scan_list if x.name == input_calibrator]
        ## Order by SNR
        calibrator_scans.sort(key=lambda x: np.nanmedian(x.snr),\
                   reverse=True)
        
        calibrator_scans = [calibrator_scans[0]]
        t7 = time.time()

        for pipeline_log in log_list:
            pipeline_log.write('\nThe chosen scan for calibration is:\n')
            pipeline_log.write(str(calibrator_scans[0].name) + '\tSNR: ' \
                                + '{:.2f}.'.format(np.nanmedian(calibrator_scans[0].snr)))
            pipeline_log.write('\nSN#1 created.\n')
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t7-t6))

        print('\nThe chosen scan for calibration is:\n')
        print(str(calibrator_scans[0].name) + '\tSNR: ' \
                        + '{:.2f}.'.format(np.nanmedian(calibrator_scans[0].snr)))
        print('\nSN#1 created.\n')
        print('Execution time: {:.2f} s. \n'.format(t7-t6))

        scan_dict = \
            {scan.time: (scan.name, inst.ddhhmmss(scan.time).tolist(), np.nanmedian(scan.snr), scan.antennas) for scan in scan_list}
        calibscans_dict = \
            {scan.time: (scan.name, inst.ddhhmmss(scan.time).tolist(), np.nanmedian(scan.snr), scan.calib_antennas) for scan in calibrator_scans}

        stats_df['SNR_scan_list'] = json.dumps(scan_dict)
        stats_df['selected_scans'] = json.dumps(calibscans_dict)
        stats_df['calibrator_search'] = 'MANUAL'
        stats_df['time_10'] = t7 - t6


    ## Digital sampling correction ##
    disp.write_box(log_list, 'Digital sampling corrections')
    disp.print_box('Digital sampling corrections')
    
    accr.sampling_correct(uvdata)
    t8 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nDigital sampling corrections applied!\nSN#2 and CL#5'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t8-t7))
    print('\nDigital sampling corrections applied!\nSN#2 and CL#5 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t8-t7))

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=5, flagver=2)
    for i, target in enumerate(target_list):
        cl5 = AIPSUVData(target, 'PLOT', uvdata.disk, 5)
        vis_cl5 = expo.vis_count(cl5)
        stats_df.at[i, 'CL5_vis'] = int(vis_cl5)
        print(f"CL5 visibilities of {target}: {vis_cl5}\n")

    stats_df['time_11'] = t8 - t7

    ## Instrumental phase correction ##
    disp.write_box(log_list, 'Instrumental phase corrections')
    disp.print_box('Instrumental phase corrections')
    
    inst.manual_phasecal_multi(uvdata, refant, calibrator_scans)
    t9 = time.time()
    
    for pipeline_log in log_list:
        pipeline_log.write('\nInstrumental phase correction applied using'\
                        + ' the calibrator(s).\nSN#3 and CL#6 created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t9-t8))
    print('\nInstrumental phase correction applied using the calibrator(s).'\
          + '\nSN#3 and CL#6 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t9-t8))

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=6, flagver=2)
    for i, target in enumerate(target_list):
        cl6 = AIPSUVData(target, 'PLOT', uvdata.disk, 6)
        vis_cl6 = expo.vis_count(cl6)
        stats_df.at[i, 'CL6_vis'] = int(vis_cl6)
        print(f"CL6 visibilities of {target}: {vis_cl6}\n")

    stats_df['time_12'] = t9 - t8


    ## Bandpass correction ##
    disp.write_box(log_list, 'Bandpass correction')
    disp.print_box('Bandpass correction')
    
    bpas.bp_correction(uvdata, refant, calibrator_scans)
    t10 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nBandpass correction applied!\nBP#1 created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t10-t9))
    print('\nBandpass correction applied!\nBP#1 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t10-t9))

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=6, flagver=2, bpass = True, \
                    keep = True)
    for i, target in enumerate(target_list):
        cl6_bp1 = AIPSUVData(target, 'PLOTBP', uvdata.disk, 6)
        vis_cl6_bp1 = expo.vis_count(cl6_bp1)
        stats_df.at[i, 'CL6_BP1_vis'] = int(vis_cl6_bp1)
        print(f"CL6 + BP1 visibilities of {target}: {vis_cl6_bp1}\n")

    stats_df['time_13'] = t10 - t9


    ## Correcting autocorrelations ##
    disp.write_box(log_list, 'Correcting autocorrelations')
    disp.print_box('Correcting autocorrelations')

    accr.correct_autocorr(uvdata)
    t11 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nAutocorrelations have been normalized!\nSN#4 and CL#7'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t11-t10))
    print('\nAutocorrelations have been normalized!\nSN#4 and CL#7 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t11-t10))

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=7, flagver=2, bpass = True)
    for i, target in enumerate(target_list):
        cl7_bp1 = AIPSUVData(target, 'PLOTBP', uvdata.disk, 7)
        vis_cl7_bp1 = expo.vis_count(cl7_bp1)
        stats_df.at[i, 'CL7_BP1_vis'] = int(vis_cl7_bp1)
        print(f"CL7 + BP1 visibilities of {target}: {vis_cl7_bp1}\n")

    stats_df['time_14'] = t11 - t10


    ## Amplitude calibration ##
    disp.write_box(log_list, 'Amplitude calibration')
    disp.print_box('Amplitude calibration')
    
    ampc.amp_cal(uvdata)
    t12 = time.time()
    for pipeline_log in log_list:
        pipeline_log.write('\nAmplitude calibration applied!\nSN#5 and CL#8'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s.\n'.format(t12-t11))
    print('\nAmplitude calibration applied!\nSN#5 and CL#8 created.\n')
    print('Execution time: {:.2f} s.\n'.format(t12-t11))

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=8, flagver=2, bpass = True)
    for i, target in enumerate(target_list):
        cl8_bp1 = AIPSUVData(target, 'PLOTBP', uvdata.disk, 8)
        vis_cl8_bp1 = expo.vis_count(cl8_bp1)
        stats_df.at[i, 'CL8_BP1_vis'] = int(vis_cl8_bp1)
        print(f"CL8 + BP1 visibilities of {target}: {vis_cl8_bp1}\n")

    stats_df['time_15'] = t12 - t11
    
    ## Get optimal solution interval for each target
    disp.write_box(log_list, 'Target fringe fit')
    disp.print_box('Target fringe fit')

    # If there are no phase reference sources, make the length of the list match the 
    # target list length
    if phase_ref == ['NONE']:
        phase_ref = ['NONE'] * len(target_list)
    
    solint_list = []
    for i, target in enumerate(target_list):
        #target_optimal_scans = opti.get_optimal_scans(target, optimal_scan_list, \
        #                                          full_source_list)
        #if target_optimal_scans == 404:
        #    solint_list.append(opti.get_scan_length(uvdata,target))
        #    log_list[i].write('\nThere were no optimal scans for the target. The chosen '\
        #                     + 'solution interval is the scan length, '\
        #                     + str(solint_list[i]) + ' minutes. \n')
        #    
        #    print('\nThere were no optimal scans for ' + target + '. The chosen '\
        #         + 'solution interval is the scan length, ' + str(solint_list[i]) \
        #         + ' minutes. \n')
        if phase_ref[i] == 'NONE':
            target_scans = [x for x in scan_list if x.name == target]

            solint, solint_dict = opti.optimize_solint_mm(uvdata, target, \
                                                       target_scans, refant)

            solint_list.append(solint)
            # Don't allow for solution intervals shorter than 1 minute

            if solint_list[i] < 1:
                solint_list[i] = 1

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

            stats_df.at[i, 'solint'] = solint_list[i]
            stats_df.at[i, 'solint_dict'] = json.dumps(solint_dict)        
        else:
            phase_ref_scans = [x for x in scan_list if x.name == phase_ref[i]]

            solint, solint_dict = opti.optimize_solint_mm(uvdata, phase_ref[i], \
                                                    phase_ref_scans, refant)

            solint_list.append(solint)
            
            # Don't allow for solution intervals shorter than 1 minute

            if solint_list[i] < 1:
                solint_list[i] = 1

            if solint_list[i] != 1:
                log_list[i].write('\nThe optimal solution interval for the phase ' \
                                + 'calibrator is ' + str(solint_list[i]) + ' minutes. \n')
                print('\nThe optimal solution interval for the phase calibrator is ' \
                    + str(solint_list[i]) + ' minutes. \n')
            else:
                log_list[i].write('\nThe optimal solution interval for the phase ' \
                                + 'calibrator is ' + str(solint_list[i]) + ' minute. \n')
                print('\nThe optimal solution interval for the phase calibrator is ' \
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
   
    ## I NEED TO PRINT SOMETHING IF THERE ARE NO SOLUTIONS AT ALL ##
    for i, target in enumerate(target_list): 
        if phase_ref[i] == 'NONE':
            stats_df.at[i,'phaseref_ff'] = False
            try:
                tfring_params = frng.target_fring_fit(uvdata, refant, target, \
                                                    solint=float(solint_list[i]), \
                                                    version = 9+i)
            
                log_list[i].write('\nFringe search performed on ' + target + '. Windows '\
                                  + 'for the search were ' + tfring_params[1] \
                                  + ' ns and ' + tfring_params[2] + ' mHz.\n')
                
                print('\nFringe search performed on ' + target + '. Windows for ' \
                    + 'the search were ' + tfring_params[1] + ' ns and ' \
                    + tfring_params[2] + ' mHz.\n')
                
                ## Get the ratio of bad to good solutions ##
        
                badsols, totalsols, ratios_dict = frng.assess_fringe_fit(uvdata, log_list[i], version = 6+i) 
                ratio = 1 - badsols/totalsols

            except RuntimeError:

                print("Fringe fit has failed.\n")

                log_list[i].write("Fringe fit has failed.\n")
                ratio = 0    
                
            # If the ratio is > 0.99, apply the solutions to a CL table

            if ratio >= 0.99:
                frng.fringe_clcal(uvdata, target, version = 9+i)

            # If the ratio is < 0.99 (arbitrary) repeat the fringe fit but averaging IFs

            if ratio < 0.99:

                print('Ratio of good/total solutions is : {:.2f}.\n'.format(ratio))
                print('Repeating the fringe fit solving for all IFs together:\n')

                log_list[i].write('Ratio of good/total solutions ' \
                                + 'is : {:.2f}.\n'.format(ratio))
                log_list[i].write('Repeating the fringe fit solving for all IFs ' \
                                + 'together:\n')

                try:
                    tfring_params = frng.target_fring_fit(uvdata, refant, target, \
                                                    solint=float(solint_list[i]), 
                                                    version = 9+i+1, solve_ifs=False)
                    
                    log_list[i].write('\nFringe search performed on ' + target \
                    + '. Windows for the search were ' + tfring_params[1] + ' ns and ' \
                    + tfring_params[2] + ' mHz.\n')
                    
                    print('\nFringe search performed on ' + target + '. Windows for ' \
                        + 'the search were ' + tfring_params[1] + ' ns and ' \
                        + tfring_params[2] + ' mHz.\n')
                        
                    ## Get the new ratio of bad to good solutions ##
                
                    badsols_s, totalsols_s, ratios_dict_s = frng.assess_fringe_fit(uvdata, log_list[i], \
                                                                version = 6+i+1) 
                    
                    ratio_single = 1 - badsols_s/totalsols_s
                    
                except RuntimeError:
                    print('\nThe new fringe fit has failed, the previous one will ' \
                         + 'be kept.\n')

                    log_list[i].write('\nThe new fringe fit has failed, the previous ' \
                                     + 'one will be kept.\n')
                    ratio_single = 0

                
                # If both ratios are 0, end the pipeline
                if (ratio + ratio_single) == 0:

                    print('\nThe pipeline was not able to find any good solutions.\n')

                    log_list[i].write('\nThe pipeline was not able to find any good ' \
                                    + 'solutions.\n')
                    
                    ## Total execution time ##
                    tf = time.time()
                    log_list[i].write('\nScript run time: '\
                                        + '{:.2f} s. \n'.format(tf-t_i))
                    # log_list[i].close()
                    ## Remove target from the workflow
                    ignore_list.append(target_list[i])
                    # target_list[i] = 'IGNORE'
                    #log_list.remove(log_list[i])
    
                
                # If the new ratio is smaller or equal than the previous, 
                # then keep the previous

                if ratio_single <= ratio:
                    print("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    print("The multi-IF fringe fit will be applied.\n")

                    log_list[i].write("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    log_list[i].write("The multi-IF fringe fit will be applied.\n ")
                    frng.fringe_clcal(uvdata, target, version = 9+i)
                    # Remove the single-IF fringe fit SN table
                    uvdata.zap_table('SN', 6+i+1)


                # If new ratio is better than the previous, then replace the SN table and 
                # apply the solutions
                if ratio_single > ratio:
                    print("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    print("The averaged IF fringe fit will be applied.\n ")

                    log_list[i].write("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    log_list[i].write("The averaged IF fringe fit will be applied.\n ")
                    uvdata.zap_table('SN', 6+i)
                    tysm.tacop(uvdata, 'SN', 6+i+1, 6+i)
                    frng.fringe_clcal(uvdata, target, version = 9+i)

            log_list[i].write('\nFringe fit corrections applied to the target!\n'\
                + 'SN#' + str(6+i) + ' and CL#' + str(9+i) \
                + ' created.\n')

            print('\nFringe fit corrections applied to ' + target + '!\nSN#' \
                + str(6+i) + ' and CL#' + str(9+i) + ' created.\n') 

        if phase_ref[i] != 'NONE':
            stats_df.at[i,'phaseref_ff'] = True
            try:
                tfring_params = frng.target_fring_fit(uvdata, refant, phase_ref[i], \
                                                    solint=float(solint_list[i]), \
                                                    version = 9+i)
            
                log_list[i].write('\nFringe search performed on the phase calibrator: ' \
                                  + phase_ref[i] + '. Windows '\
                                  + 'for the search were ' + tfring_params[1] \
                                  + ' ns and ' + tfring_params[2] + ' mHz.\n')
                
                print('\nFringe search performed on the phase calibrator: ' \
                    + phase_ref[i] \
                    + '. Windows for the search were ' + tfring_params[1] + ' ns and ' \
                    + tfring_params[2] + ' mHz.\n')
                
                ## Get the ratio of bad to good solutions ##
        
                badsols, totalsols, ratios_dict = frng.assess_fringe_fit(uvdata, log_list[i], version = 6+i) 
                ratio = 1 - badsols/totalsols

            except RuntimeError:

                print("Fringe fit has failed.\n")

                log_list[i].write("Fringe fit has failed.\n")
                ratio = 0      


            # If the ratio is > 0.99, apply the solutions to a CL table

            if ratio >= 0.99:
                frng.fringe_phaseref_clcal(uvdata, target, version = 9+i)

            # If the ratio is < 0.99 (arbitrary) repeat the fringe fit but averaging IFs

            if ratio < 0.99:

                print('Ratio of good/total solutions is : {:.2f}.\n'.format(ratio))
                print('Repeating the fringe fit solving for all IFs together:\n')

                log_list[i].write('Ratio of good/total solutions ' \
                                + 'is : {:.2f}.\n'.format(ratio))
                log_list[i].write('Repeating the fringe fit solving for all IFs ' \
                                + 'together:\n')

                try:
                    tfring_params = frng.target_fring_fit(uvdata, refant, phase_ref[i], \
                                                    solint=float(solint_list[i]), 
                                                    version = 9+i+1, solve_ifs=False)
                    
                    log_list[i].write('\nFringe search performed on the phase ' \
                                    + 'calibrator: ' + phase_ref[i] + '. Windows '\
                                    + 'for the search were ' + tfring_params[1] \
                                    + ' ns and ' + tfring_params[2] + ' mHz.\n')
                    
                    print('\nFringe search performed on the phase calibrator: ' \
                        + phase_ref[i] \
                        + '. Windows for the search were ' + tfring_params[1] \
                        + ' ns and ' + tfring_params[2] + ' mHz.\n')
                        
                    ## Get the new ratio of bad to good solutions ##
                
                    badsols_s, totalsols_s, ratios_dict_s = frng.assess_fringe_fit(uvdata, log_list[i], \
                                                                version = 6+i+1) 
                    ratio_single = 1 - badsols_s/totalsols_s
                    
                except RuntimeError:
                    print('\nThe new fringe fit has failed, the previous one will ' \
                         + 'be kept.\n')

                    log_list[i].write('\nThe new fringe fit has failed, the previous ' \
                                     + 'one will be kept.\n')
                    ratio_single = 0

                
                # If both ratios are 0, end the pipeline
                if (ratio + ratio_single) == 0:
                    print('\nThe pipeline was not able to find any good solutions.\n')

                    log_list[i].write('\nThe pipeline was not able to find any good ' \
                                    + 'solutions.\n')
                    
                    ## Total execution time ##
                    tf = time.time()
                    log_list[i].write('\nScript run time: '\
                                        + '{:.2f} s. \n'.format(tf-t_i))
                    # log_list[i].close()
                    ## Remove target from the workflow
                    ignore_list.append(target_list[i])
                    # target_list[i] = 'IGNORE'
                    #log_list.remove(log_list[i])
    
                
                # If the new ratio is smaller or equal than the previous, 
                # then keep the previous

                if ratio_single <= ratio:
                    print("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    print("The multi-IF fringe fit will be applied.\n ")

                    log_list[i].write("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    log_list[i].write("The multi-IF fringe fit will be applied.\n ")
                    frng.fringe_phaseref_clcal(uvdata, target, version = 9+i)
                    # Remove the single-IF fringe fit SN table
                    uvdata.zap_table('SN', 6+i+1)


                # If new ratio is better than the previous, then replace the SN table and 
                # apply the solutions
                if ratio_single > ratio:
                    print("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    print("The averaged IF fringe fit will be applied.\n ")

                    log_list[i].write("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    log_list[i].write("The averaged IF fringe fit will be applied.\n ")
                    uvdata.zap_table('SN', 6+i)
                    tysm.tacop(uvdata, 'SN', 6+i+1, 6+i)
                    frng.fringe_phaseref_clcal(uvdata, target, version = 9+i)

            log_list[i].write('\nFringe fit corrections applied to the target!\n'\
                + 'SN#' + str(6+i) + ' and CL#' + str(9+i) \
                + ' created.\n')

            print('\nFringe fit corrections applied to ' + target + '!\nSN#' \
                + str(6+i) + ' and CL#' + str(9+i) + ' created.\n')
            
        if ratio < 0.99: 
            stats_df.at[i, 'good_sols'] = totalsols - badsols
            stats_df.at[i, 'total_sols'] = totalsols
            stats_df.at[i, 'ratios_dict'] = json.dumps(ratios_dict)
            stats_df.at[i, 'good_sols_single'] = totalsols_s - badsols_s
            stats_df.at[i, 'total_sols_single'] = totalsols_s
            stats_df.at[i, 'ratios_dict_single'] = json.dumps(ratios_dict_s)

        if ratio >= 0.99: 
            stats_df.at[i, 'good_sols'] = totalsols - badsols
            stats_df.at[i, 'total_sols'] = totalsols
            stats_df.at[i, 'ratios_dict'] = json.dumps(ratios_dict)
            stats_df.at[i, 'good_sols_single'] = False
            stats_df.at[i, 'total_sols_single'] = False
            stats_df.at[i, 'ratios_dict_single'] = False

    # Counting visibilities
    expo.data_split(uvdata, target_list, cl_table=9, flagver=2, bpass = True)
    for i, target in enumerate(target_list):
        cl9_bp1 = AIPSUVData(target, 'PLOTBP', uvdata.disk, 9)
        vis_cl9_bp1 = expo.vis_count(cl9_bp1)
        stats_df.at[i, 'CL9_BP1_vis'] = int(vis_cl9_bp1)
        print(f"CL9 + BP1 visibilities of {target}: {vis_cl9_bp1}\n")


    t14 = time.time()
    for i, pipeline_log in enumerate(log_list):        
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t14-t13))  
    print('Execution time: {:.2f} s. \n'.format(t14-t13))

    stats_df['time_17'] = t14 - t13

    ##  Export data ##
    t_export = time.time()
    disp.write_box(log_list, 'Exporting visibility data')
    disp.print_box('Exporting visibility data')

    no_baseline = expo.data_export(path_list, uvdata, target_list, filename_list, \
                                  flag_frac = flag_edge)


    for i, target in enumerate(target_list): 
        if target in ignore_list:
            stats_df.at[i, 'exported_size'] = 0
            continue
        if target not in no_baseline:
            log_list[i].write('\n' + target + ' visibilites exported to ' \
                              + filename_list[i]  + '.uvfits\n')
            print('\n' + target + ' visibilites exported to ' + filename_list[i] \
                            + '.uvfits\n')
            
            stats_df.at[i, 'exported_size_mb'] = \
                os.path.getsize(path_list[i] + '/' + filename_list[i] + '.uvfits')/1024**2

        else:
            stats_df.at[i, 'exported_size'] = 0
            log_list[i].write('\n' + target + ' visibilites could not be exported, ' \
                              + 'there are not enough solutions to form a baseline.\n')
            print('\n' + target + ' visibilites could not be exported, ' \
                              + 'there are not enough solutions to form a baseline.\n')


            

    expo.table_export(path_list, uvdata, target_list, filename_list)
    for i, target in enumerate(target_list): 
        log_list[i].write('\n' + target + ' calibration tables exported to /TABLES/' \
                          + filename_list[i] + '.caltab.uvfits\n')
        print('\n' + target + ' calibration tables exported to /TABLES/' \
              + filename_list[i] + '.caltab.uvfits\n')
        
    stats_df['time_18'] = time.time() - t_export

    ## PLOTS ##

    ######################## TEST FOR THE GUI ########################
    disp.print_box("Generating interactive plots")
    #
    interactive = True
    if interactive ==  True:
        plot.generate_pickle_plots(uvdata, target_list)

    ######################## TEST FOR THE GUI ########################

    t_plots = time.time()

    ## Plot visibilities as a function of frequency of target and calibrator ## 
    disp.write_box(log_list, 'Plotting visibilities')
    disp.print_box('Plotting visibilities')
    
    ## Uncalibrated ##
    for i, target in enumerate(target_list):
        #if target in ignore_list:
        #    continue
        #if target not in no_baseline:
            plot_check = 0
            plot_check = plot.possm_plotter(path_list[i], uvdata, target, 
                                            calibrator_scans, 1, bpver = 0, \
                                            flagver=1, flag_edge=False)
            if plot_check == 999:
                log_list[i].write('\nUncalibrated visibilities could not be plotted!\n')
                print('\nUncalibrated visibilities could not be plotted!\n')
            else:
                log_list[i].write('\nUncalibrated visibilities plotted in /PLOTS/'  \
                                + filename_list[i] + '_CL1_POSSM.ps\n')
                print('\nUncalibrated visibilities plotted in /PLOTS/'  \
                                + filename_list[i] + '_CL1_POSSM.ps\n')
        
    ## Calibrated ##
    for i, target in enumerate(target_list):
        if target in ignore_list:
            continue
        if target not in no_baseline:    
            plot_check = 0    
            plot_check = plot.possm_plotter(path_list[i], uvdata, target, 
                                            calibrator_scans, 9+i, bpver = 1, 
                                            flag_edge=False)
            if plot_check == 999:
                log_list[i].write('\nUncalibrated visibilities could not be plotted!\n')
                print('\nUncalibrated visibilities could not be plotted!\n')
            else:
                log_list[i].write('Calibrated visibilities plotted in /PLOTS/' \
                                + filename_list[i] + '_CL' + str(9+i) + '_POSSM.ps\n')
                print('Calibrated visibilities plotted in /PLOTS/' \
                                + filename_list[i] + '_CL' + str(9+i) + '_POSSM.ps\n')
        
    ## Plot uv coverage ##
    for i, target in enumerate(target_list):
        if target in ignore_list:
            continue
        if target not in no_baseline:
            plot_check = 0
            plot_check = plot.uvplt_plotter(path_list[i], uvdata, target)
            if plot_check == 999:
                log_list[i].write('UV coverage could not be plotted\n')
                print('UV coverage could not be plotted!\n')    
            else:
                log_list[i].write('UV coverage plotted in /PLOTS/' \
                                + filename_list[i] + '_UVPLT.ps\n')
                print('UV coverage plotted in /PLOTS/' + filename_list[i] + '_UVPLT.ps\n')
        
    ## Plot visibilities as a function of time of target ## 
    for i, target in enumerate(target_list):
        if target in ignore_list:
            continue
        if target not in no_baseline:
            plot_check = 0
            plot_check = plot.vplot_plotter(path_list[i], uvdata, target, 9+i)     
            if plot_check == 999:
                log_list[i].write('Visibilities as a function of time could not be ' \
                                  + 'plotted!\n')
                print('Visibilities as a function of time could not be plotted!\n')
            else:
                log_list[i].write('Visibilities as a function of time plotted in /PLOTS/' \
                                + filename_list[i]  + '_VPLOT.ps\n')
                print('Visibilities as a function of time plotted in /PLOTS/' \
                                + filename_list[i]  + '_VPLOT.ps\n')
                
    ## Plot visibilities as a function of uv distance of target ##
    for i, target in enumerate(target_list):
        fig = pickle.load(open(f'../tmp/{target}.radplot.pickle', 'rb'))
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

        fig.tight_layout()
        fig.savefig(f'{path_list[i]}/PLOTS/{filename_list[i]}_RADPLOT.pdf', bbox_inches='tight')
                
        
    for i, target in enumerate(target_list):
        plot_size = sum(f.stat().st_size for f in Path(path_list[i] + '/PLOTS/').rglob('*') if f.is_file())
        stats_df.at[i, 'plot_size_mb'] = plot_size / 1024**2

    t15 = time.time()
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s.\n'.format(t15-t14))
    print('Execution time: {:.2f} s.\n'.format(t15-t14))

    stats_df['time_19'] = t15 - t_plots

    ## Total execution time ##
    tf = time.time()
    for pipeline_log  in log_list:
        pipeline_log.write('\nScript run time: '\
                         + '{:.2f} s.\n'.format(tf-t_i))
        pipeline_log.close()
    print('\nScript run time: {:.2f} s.\n'.format(tf-t_i))

    ######################## TEST FOR STATS ########################

    stats_df['total_time'] = tf - t_i
    for i, path in enumerate(path_list):
        stats_df.transpose().to_csv(f'{path}/{filename_list[i]}.stats.csv')

    ######################## TEST FOR STATS ########################   

def pipeline(input_dict):
    """Read the inputs, split multiple frequencies and calibrate the dataset

    :param input_dict: _description_
    :type input_dict: _type_
    """    
    # Read logo
    ascii_logo = open('../GUI/ascii_logo_string.txt', 'r').read()

    # Read the input dictionary
    filepath_list = input_dict['paths']
    userno = input_dict['userno'] 
    AIPS.userno = userno
    target_list = input_dict['targets'] 
    disk_number = input_dict['disk'] 
    inp_cal = input_dict['calib'] 
    load_all = input_dict['load_all'] 
    shifts = input_dict['shifts'] 
    def_refant = input_dict['refant'] 
    output_directory = input_dict['output_directory'] 
    flag_edge = input_dict['flag_edge']
    phase_ref = input_dict['phase_ref']

    ## Check for multiband datasets ##
    # If multiple files, done only on the first, since all need to have the same 
    # frequency setup
    # In IDs    
    multifreq_id = load.is_it_multifreq_id(filepath_list[0])
    # In IFs
    multifreq_if = load.is_it_multifreq_if(filepath_list[0])
    # If there are multiple IDs:
    if multifreq_id[0] == True:
        for ids in range(multifreq_id[1]):

            ############################################
            ## KEEP TRACK OF ALL STATS IN A DATAFRAME ##
            ############################################
            t_0 = time.time()
            stats_df = pd.DataFrame({"target": target_list})

            ## Select sources to load ##
            full_source_list = load.get_source_list(filepath_list, multifreq_id[2][ids])
            if load_all == False:
                calibs = load.find_calibrators(full_source_list, choose = 'BYCOORD')
                # If no sources are on the calibrator list, load all and print a message
                if calibs == 999:
                    sources = [x.name for x in full_source_list]
                    load_all = True
                    print("None of the sources was found on the VLBA calibrator list." \
                         + " All sources will be loaded.\n" )
                else:
                    sources = calibs.copy()
                    sources += target_list
                    sources += [x for x in phase_ref if x!='NONE']
            if load_all == True:
                sources = [x.name for x in full_source_list]

            # STATS #
            stats_df['loaded_sources'] =  json.dumps(dict(zip(sources, [x.band_flux for x in full_source_list if x.name in sources])))            
            stats_df['n_of_freqs'] = multifreq_id[1]

            if multifreq_id[2][ids] > 1e10:
                klass_1 = str(multifreq_id[2][ids])[:2] + 'G'
            else:
                klass_1 = str(multifreq_id[2][ids])[:1] + 'G'

            # Define AIPS name
            hdul = fits.open(filepath_list[0])
            aips_name = hdul[0].header['OBSERVER'] # + '_' + klass_1

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
                filename_list[i] = load.set_name(filepath_list[0], name, klass_1)
                path_list[i] = project_dir + '/' + filename_list[i]
                if os.path.exists(project_dir + '/' + filename_list[i]) == True:
                    os.system('rm -rf ' + project_dir + '/' + filename_list[i])
                os.system('mkdir ' + project_dir + '/' + filename_list[i])
                os.system('mkdir ' + project_dir + '/' + filename_list[i] \
                          + '/PLOTS')
                os.system('mkdir ' + project_dir + '/' + filename_list[i] \
                          + '/TABLES')
                log_list[i] = open(project_dir + '/' + filename_list[i] + '/' \
                                   + filename_list[i] + '_VIPCALslog.txt', 'w+')
                log_list[i].write(ascii_logo + '\n')
                #for filepath in filepath_list:
                #    log_list[i].write(os.path.basename(filepath) + ' --- '\
                #                        + '{:.2f} MB \n'.format\
                #                        (os.path.getsize(filepath)/1024**2 ))

            stats_df['t_0'] = time.time() - t_0
            ## START THE PIPELINE ##         
            calibrate(filepath_list, aips_name_short, sources, full_source_list, \
                        target_list, filename_list, log_list, path_list, \
                        disk_number, klass = klass_1, \
                        multi_id = True, selfreq = multifreq_id[2][ids]/1e6,\
                        default_refant = def_refant, input_calibrator = inp_cal, \
                        load_all = load_all, shift_coords = shifts, \
                        phase_ref = phase_ref, flag_edge = flag_edge, stats_df = stats_df) 
            
        return() # STOP the pipeline. This needs to be tweaked.

    # If there are multiple IFs:   
    if multifreq_if[0] == True:
        
        klass_1 = multifreq_if[5] + 'G'
        klass_2 = multifreq_if[6] + 'G'

        ## FIRST FREQUENCY ##

        ############################################
        ## KEEP TRACK OF ALL STATS IN A DATAFRAME ##
        ############################################
        t_0 = time.time()
        stats_df = pd.DataFrame({"target": target_list})
        
        ## Select sources to load ##
        full_source_list = load.get_source_list(filepath_list, multifreq_if[7])
        if load_all == False:
            calibs = load.find_calibrators(full_source_list, choose = 'BYCOORD')
            # If no sources are on the calibrator list, load all and print a message
            if calibs == 999:
                sources = [x.name for x in full_source_list]
                load_all = True
                print("None of the sources was found on the VLBA calibrator list." \
                        + " All sources will be loaded.\n" )
            else:
                sources = calibs.copy()
                sources += target_list
                sources += [x for x in phase_ref if x!='NONE']
        if load_all == True:
            sources = [x.name for x in full_source_list]

        # STATS #
        stats_df['loaded_sources'] =  json.dumps(dict(zip(sources, [x.band_flux for x in full_source_list if x.name in sources])))
        stats_df['n_of_freqs'] = 2

        # Define AIPS name
        hdul = fits.open(filepath_list[0])
        aips_name = hdul[0].header['OBSERVER'] # + '_' + klass_1

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
            filename_list[i] = load.set_name(filepath_list[0], name, klass_1)
            path_list[i] = project_dir + '/' + filename_list[i]
            if os.path.exists(project_dir + '/' + filename_list[i]) == True:
                os.system('rm -rf ' + project_dir + '/' + filename_list[i])
            os.system('mkdir ' + project_dir + '/' + filename_list[i])
            os.system('mkdir ' + project_dir + '/' + filename_list[i] \
                        + '/PLOTS')
            os.system('mkdir ' + project_dir + '/' + filename_list[i] \
                        + '/TABLES')

            log_list[i] = open(project_dir + '/' + filename_list[i] + '/' \
                               + filename_list[i] + '_VIPCALslog.txt', 'w+')
            log_list[i].write(ascii_logo + '\n')

        stats_df['t_0'] = time.time() - t_0        
        ## START THE PIPELINE ##
        calibrate(filepath_list, aips_name_short, sources, full_source_list, target_list, \
                filename_list, log_list, path_list, \
                disk_number, klass = klass_1,\
                bif = multifreq_if[1], eif = multifreq_if[2], \
                default_refant = def_refant, input_calibrator = inp_cal, \
                load_all = load_all, shift_coords = shifts, flag_edge = flag_edge, \
                phase_ref = phase_ref, stats_df = stats_df)
        

        ## SECOND FREQUENCY ##

        ############################################
        ## KEEP TRACK OF ALL STATS IN A DATAFRAME ##
        ############################################
        t_0 = time.time()
        stats_df = pd.DataFrame({"target": target_list})

        ## Select sources to load ##
        full_source_list = load.get_source_list(filepath_list, multifreq_if[8])
        if load_all == False:
            calibs = load.find_calibrators(full_source_list, choose = 'BYCOORD')
            # If no sources are on the calibrator list, load all and print a message
            if calibs == 999:
                sources = [x.name for x in full_source_list]
                load_all = True
                print("None of the sources was found on the VLBA calibrator list." \
                        + " All sources will be loaded.\n" )
            else:
                sources = calibs.copy()
                sources += target_list
                sources += [x for x in phase_ref if x!='NONE']
        if load_all == True:
            sources = [x.name for x in full_source_list]

         # STATS #
        stats_df['loaded_sources'] =  json.dumps(dict(zip(sources, [x.band_flux for x in full_source_list if x.name in sources])))
                
        stats_df['n_of_freqs'] = 2
        
        # Define AIPS name
        hdul = fits.open(filepath_list[0])
        aips_name = hdul[0].header['OBSERVER'] # + '_' + klass_2
        
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
            filename_list[i] = load.set_name(filepath_list[0], name, klass_2)
            path_list[i] = project_dir + '/' + filename_list[i]
            if os.path.exists(project_dir + '/' + filename_list[i]) == True:
                os.system('rm -rf ' + project_dir + '/' + filename_list[i])
            os.system('mkdir ' + project_dir + '/' + filename_list[i])
            os.system('mkdir ' + project_dir + '/' + filename_list[i] \
                        + '/PLOTS')
            os.system('mkdir ' + project_dir + '/' + filename_list[i] \
                        + '/TABLES')

            log_list[i] = open(project_dir + '/' + filename_list[i] + '/' \
                               + filename_list[i] + '_VIPCALslog.txt', 'w+')
            log_list[i].write(ascii_logo + '\n')

        stats_df['t_0'] = time.time() - t_0           
        ## START THE PIPELINE ##  
        calibrate(filepath_list, aips_name_short, sources, full_source_list, target_list, \
                filename_list, log_list, path_list, \
                disk_number, klass = klass_2, \
                bif = multifreq_if[3], eif = multifreq_if[4], default_refant = def_refant, \
                input_calibrator = inp_cal, load_all = load_all, shift_coords = shifts,
                flag_edge = flag_edge, phase_ref = phase_ref, stats_df = stats_df) 

        # End the pipeline
        return()

     # If there is only one frequency:  
    if multifreq_id[0] == False and multifreq_if[0] == False:

        ############################################
        ## KEEP TRACK OF ALL STATS IN A DATAFRAME ##
        ############################################
        t_0 = time.time()
        stats_df = pd.DataFrame({"target": target_list})
        
        klass_1 = multifreq_if[5] + 'G'
        
        ## Select sources to load ##
        full_source_list = load.get_source_list(filepath_list)
        if load_all == False:
            calibs = load.find_calibrators(full_source_list, choose = 'BYCOORD')
            # If no sources are on the calibrator list, load all and print a message
            if calibs == 999:
                sources = [x.name for x in full_source_list]
                load_all = True
                print("None of the sources was found on the VLBA calibrator list." \
                        + " All sources will be loaded.\n" )
            else:
                sources = calibs.copy()
                sources += target_list
                sources += [x for x in phase_ref if x!='NONE']
        if load_all == True:
            sources = [x.name for x in full_source_list]

        # STATS #
        stats_df['loaded_sources'] =  json.dumps(dict(zip(sources, [x.band_flux for x in full_source_list if x.name in sources])))
        stats_df['n_of_freqs'] = 1

        # Define AIPS name
        hdul = fits.open(filepath_list[0])
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
            filename_list[i] = load.set_name(filepath_list[0], name, klass_1)
            path_list[i] = project_dir + '/' + filename_list[i]
            
            if os.path.exists(project_dir + '/' + filename_list[i]) == True:
                os.system('rm -rf ' + project_dir + '/' + filename_list[i])
            os.system('mkdir ' + project_dir + '/' + filename_list[i])
            os.system('mkdir ' + project_dir + '/' + filename_list[i] \
                        + '/PLOTS')
            os.system('mkdir ' + project_dir + '/' + filename_list[i] \
                        + '/TABLES')

            log_list[i] = open(project_dir + '/' + filename_list[i] + '/' \
                               + filename_list[i] + '_VIPCALslog.txt', 'w+')
            log_list[i].write(ascii_logo + '\n')

        stats_df['t_0'] = time.time() - t_0            
        ## START THE PIPELINE ##               
        calibrate(filepath_list, aips_name, sources, full_source_list, target_list, \
                filename_list, log_list, path_list, \
                disk_number, klass = klass_1, default_refant = def_refant, \
                input_calibrator = inp_cal, load_all = load_all, shift_coords = shifts,
                flag_edge = flag_edge, phase_ref = phase_ref, stats_df = stats_df)   