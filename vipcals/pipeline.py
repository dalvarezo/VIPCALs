import os
import time 
import numpy as np
from datetime import datetime

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

def calibrate(filepath_list, aips_name, sources, full_source_list, target_list, \
             filename_list, log_list, path_list,\
             disk_number, klass = '', seq = 1, bif = 0, eif = 0, \
             multi_id = False, selfreq = 0, default_refant = 'NONE', \
             input_calibrator = 'NONE', load_all = False, shift_coords = 'None',
             flag_edge = 0, phase_ref = ['NONE']):
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
    
    ## Check if the filepath is > 46 characters
    ## IN PRINCIPLE THIS PART IS NOT NEEDED ANYMORE, SYMLINKS ARE ALWAYS USED INSTEAD
    ## OF THE ORIGINAL FILE
    
    #if len(filepath.split('/')[-1]) > 46:
 
        # directory = '/'.join(filepath.split('/')[:-1])
        # This would be the ideal, to create the hard link in the same 
        # directory where the file is located. In gunmen I cannot do 
        # this, since I have no write permission in for example 
        # /data/pipeline_test_sample/felix/
        # To keep it simple, for now, the hard link is created always 
        # in /data/pipeline_test_sample
        
    #    directory = '/data/pipeline_test_sample'        

        ## Create hard link to a shorter path
        
        # Delete if it already exists
    #    if os.path.exists(directory + '/aux.uvfits'):
    #        os.system('rm ' + directory + '/aux.uvfits')
        
    #    os.system('ln ' + filepath + ' ' + directory + '/aux.uvfits')
    #    shortpath = directory + '/aux.uvfits'
        
        ## Load the dataset ##
    #    t0 = time.time()
    #    load.load_data(shortpath, aips_name, sources, disk_number, multi_id,\
    #    selfreq, klass = klass, bif = bif, eif = eif, l_a = load_all)
    #    t1 = time.time()   
    #    os.system('rm ' + shortpath)

    #else:

    ## Load the dataset ##
    t0 = time.time()
    load.load_data(filepath_list, aips_name, sources, disk_number, multi_id,\
    selfreq, klass = klass, bif = bif, eif = eif, l_a = load_all)
    t1 = time.time() 
 
    for pipeline_log in log_list:
        pipeline_log.write('\nData loaded! The loaded sources are ' + \
                        str(list(set(sources))) + '.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t1-t0))
    print('\nData loaded! The loaded sources are', list(set(sources)) ,'.\n')
    print('Execution time: {:.2f} s. \n'.format(t1-t0))

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
    
    ## Check for CL/NX tables
    if [1, 'AIPS CL'] not in uvdata.tables or [1, 'AIPS NX'] not in \
        uvdata.tables:
        tabl.run_indxr(uvdata)
        print('\nINDXR was run, NX#1 and CL#1 were created.\n')

    ## Check for TY/GC/FG tables
    missing_tables = False
    if ([1, 'AIPS TY'] not in uvdata.tables or [1, 'AIPS GC'] \
    not in uvdata.tables or [1, 'AIPS FG'] not in uvdata.tables):
        disp.write_box(log_list, 'Loading external table information')
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
            os.system('cp ./tsys.vlba ' + path + '/tsys.vlba')
    
        # And delete the files from the current directory
        os.system('rm ./tables*')
        os.system('rm ./tsys.vlba')
   
        print('\nSystem temperatures were not available in the file, they ' \
               + 'have been retrieved online.\n')
        print('TY#1 created.\n')
        
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
                               + 'file, it has been retrieved from ' + good_url \
                               + '\nGC#1 created.\n\n')
            
        # Move the gain curve file to the target folders
        for path in path_list:
            os.system('cp ./gaincurves.vlba ' + path + '/gaincurves.vlba')
    
        # And delete the files from the main directory
        os.system('rm ./gaincurves.vlba')           
        
        print('\nGain curve information was not available in the file, it has '\
          + 'been retrieved from ' + good_url + '\nGC#1 created.\n')
        
        
    if [1, 'AIPS FG'] not in uvdata.tables:
        retrieved_urls = tabl.load_fg_tables(uvdata)
        for pipeline_log in log_list:
            for good_url in retrieved_urls:
                pipeline_log.write('Flag information was not available in the file, ' \
                                    + 'it has been retrieved from ' + good_url + '\n')
            pipeline_log.write('FG#1 created.\n')

        # Move the flag file to the target folders
        for path in path_list:
            os.system('cp ./flags.vlba ' + path + '/flags.vlba')
    
        # And delete the files from the main directory
        os.system('rm ./tables*')
        os.system('rm ./flags.vlba')

        print('\nFlag information was not available in the file, it ' \
               + 'has been retrieved online.\n')
        print('FG#1 created.\n')

    if missing_tables == True:
        t1 = time.time()
        for pipeline_log in log_list:
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t1-t_i_table))


    ## Shift phase center if necessary ##
    # No shift will be done if the new coordinates are 0h0m0s +0d0m0s, in that case the
    # source will not be altered

    if shift_coords != 'NONE':
        disp.write_box(log_list, 'Shifting phase center')
        print('\nShifting phase center\n')
        for i, target in enumerate(target_list):
            if shift_coords[i] == SkyCoord(0, 0, unit = 'deg'):
                continue
                
            old_seq = uvdata.seq    
            # Delete the data if it already existed
            if AIPSUVData(uvdata.name, uvdata.klass, \
                          uvdata.disk, uvdata.seq + 1).exists(): 
                AIPSUVData(uvdata.name, uvdata.klass, \
                          uvdata.disk, uvdata.seq + 1).zap()
            # Shift
            shft.uv_shift(uvdata, target, shift_coords[i])
         
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
    # Update the sequence
    seq = uvdata.seq
    
    ## If the time resolution is < 0.99s, average the dataset in time
    try:
        time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'][0])
    except TypeError: # Single IF datasets
        time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'])
        
    if time_resol < 0.99:
        avgdata = AIPSUVData(aips_name, 'AVGT', disk_number, seq)
        if avgdata.exists() == True:
            avgdata.zap()
        tabl.time_aver(uvdata, time_resol, 2)
        uvdata = AIPSUVData(aips_name, 'AVGT', disk_number, seq)

        # Index the data again
        uvdata.zap_table('CL', 1)
        tabl.run_indxr(uvdata)

        disp.write_box(log_list, 'Data averaging')
        for pipeline_log in log_list:
            pipeline_log.write('\nThe time resolution was ' \
                            + '{:.2f}'.format(time_resol) \
                            + 's. It has been averaged to 2s.\n')
        print('\nThe time resolution was {:.2f}'.format(time_resol) \
            + 's. It has been averaged to 2s.\n')
        
            
    ## If the channel bandwidth is smaller than or equal to 0.5 MHz, average the dataset 
    ## in frequency up to 0.5 MHz per channel 
    try:
        ch_width = float(uvdata.table('CQ', 1)[0]['chan_bw'][0])
        no_chan = int(uvdata.table('CQ', 1)[0]['no_chan'][0])
    except TypeError: # Single IF datasets
        ch_width = float(uvdata.table('CQ', 1)[0]['chan_bw'])
        no_chan = int(uvdata.table('CQ', 1)[0]['no_chan'])
        
    if ch_width < 500000:
        avgdata = AIPSUVData(aips_name, 'AVGF', disk_number, seq)
        if avgdata.exists() == True:
            avgdata.zap()
        ratio = 500000/ch_width    # NEED TO ADD A CHECK IN CASE THIS FAILS
        
        if time_resol >= 0.33: # => If it was not written before
            disp.write_box(log_list, 'Data averaging')
        
        tabl.freq_aver(uvdata,ratio)
        uvdata = AIPSUVData(aips_name, 'AVGF', disk_number, seq)

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


    ## Print scan information ##    
    load.print_listr(uvdata, path_list, filename_list)
    for i, pipeline_log in enumerate(log_list):
        pipeline_log.write('\nScan information printed in ' + path_list[i] + '/' \
                            + filename_list[i] + '_scansum.txt \n')
    ## Smooth the TY table ##  
    ## Flag antennas with no TY or GC table entries ##  
    
    disp.write_box(log_list, 'Flagging system temperatures')
    
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

            
    
    original_tsys, flagged_tsys = tysm.ty_assess(uvdata)
    
    # Maybe this output could be written as a %, I just need to manually write
    # the case where 0 points are flagged
    for pipeline_log in log_list:
        pipeline_log.write('\nSystem temperatures clipped! ' + str(flagged_tsys) \
                        + ' Tsys points out of a total of ' \
                        + str(original_tsys) + ' have been flagged. '\
                        + 'TY#2 created.\n')
     
    print('\nSystem temperatures clipped! ' + str(flagged_tsys) \
          + ' Tsys points out of a total of ' \
          + str(original_tsys) + ' have been flagged. '\
          + 'TY#2 created.\n')
    
    
    t2 = time.time()  

    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t2-t1))
    print('Execution time: {:.2f} s. \n'.format(t2-t1))

    # full_source_list needs to be re-written after loading, to avoid issues when 
    # concatenating files
    full_source_list = load.redo_source_list(uvdata)

    ## Choose refant ##
    disp.write_box(log_list, 'Reference antenna search')
    
    if default_refant == 'NONE':
        ## TESTING ##
        ## Now it prints the results using only the targets and all sources ##
        ## and repeats this search just before the very last fringe fit ##
        #for pipeline_log in log_list:
        #    pipeline_log.write('\nCHOOSING REFANT WITH TARGETS\n')
        ## FOR THE TARGETS ##
        #refant = rant.refant_choose_snr(uvdata, sources, target_list, target_list, \
        #                                full_source_list, log_list)
        ## FOR ALL SOURCES ##
        for pipeline_log in log_list:
            pipeline_log.write('\nCHOOSING REFANT WITH ALL SOURCES\n')
        refant = rant.refant_choose_snr(uvdata, sources, sources, target_list, \
                                        full_source_list, log_list, load_all)
    else:
        refant = [x['nosta'] for x in uvdata.table('AN',1) \
                  if default_refant in x['anname']][0]
        for pipeline_log in log_list:
            pipeline_log.write(default_refant + ' has been manually selected as the ' \
                               + 'reference antenna.\n')
        print(default_refant + ' has been manually selected as the reference antenna.\n')

    t3=time.time()
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t3-t2))
    print('Execution time: {:.2f} s. \n'.format(t3-t2))

    ## Ionospheric correction ##
    disp.write_box(log_list, 'Ionospheric corrections')
    
    YYYY = int(uvdata.header.date_obs[:4])
    MM = int(uvdata.header.date_obs[5:7])
    DD = int(uvdata.header.date_obs[8:])
    date_obs = datetime(YYYY, MM, DD)
    if date_obs > datetime(1998,6,1):
        iono.ionos_correct(uvdata)
        t4 = time.time()
        for pipeline_log in log_list:
            pipeline_log.write('\nIonospheric corrections applied! CL#2 created.'\
                            + '\n')
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t4-t3))
        print('\nIonospheric corrections applied! CL#2 created.\n')
        print('Execution time: {:.2f} s. \n'.format(t4-t3))
        os.system('rm -rf /tmp/jplg*')
    else:
        t4 = time.time()
        iono.tacop(uvdata, 'CL', 1, 2)
        for pipeline_log in log_list:
            pipeline_log.write('\nIonospheric corrections not applied! IONEX '\
                            + 'files are not available for observations '\
                            + 'older than June 1998. CL#2 will be copied '\
                            + 'from CL#1.\n')
        print('\nIonospheric corrections not applied! IONEX files are not '\
              + 'available for observations older than June 1998. CL#2 '\
              + 'will be copied from CL#1.\n')
        
    ## Earth orientation parameters correction ##
    disp.write_box(log_list, 'Earth orientation parameters corrections')
    
    eopc.eop_correct(uvdata)
    t5 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nEarth orientation parameter corrections applied! '\
                        + 'CL#3 created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t5-t4))
    print('\nEarth orientation parameter corrections applied! CL#3 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t5-t4))
    os.system('rm -rf /tmp/usno_finals.erp')

    ## Parallatic angle correction ##
    disp.write_box(log_list, 'Parallactic angle corrections')
    
    pang.pang_corr(uvdata)
    t6 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nParallactic angle corrections applied! CL#4'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t6-t5))
    print('\nParallactic angle corrections applied! CL#4 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t6-t5))

    ## Selecting calibrator scan ##
    # If there is no input calibrator
    if input_calibrator == 'NONE':
        ## Look for calibrator ##
        ## SNR fringe search ##
        disp.write_box(log_list, 'Calibrator search')
        
        #snr_fring(uvdata, refant)
        cali.snr_fring_only_fft(uvdata, refant)
        
        ## Get a list of scans ordered by SNR ##
        
        scan_list = cali.snr_scan_list_v2(uvdata, full_source_list)
        
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
                                   + '{:.2f}.'.format(np.median(calibrator_scans[0].snr)))
                pipeline_log.write('\nSN#1 created.\n')

            else:
                pipeline_log.write('\nThe chosen scans for calibration are:\n')
                for scn in calibrator_scans:    
                    pipeline_log.write(str(scn.name) + '\tSNR: ' \
                                      + '{:.2f}.\n'.format(np.median(scn.snr)))
                pipeline_log.write('\nSN#1 created.\n')

            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t7-t6))

   
        if len(calibrator_scans) == 1:
            print('\nThe chosen scan for calibration is:\n')
            print(str(calibrator_scans[0].name) + '\tSNR: ' \
                            + '{:.2f}.'.format(np.median(calibrator_scans[0].snr)))
            print('\nSN#1 created.\n')

        else:
            print('\nThe chosen scans for calibration are:\n')
            for scn in calibrator_scans:    
                print(str(scn.name) + '\tSNR: {:.2f}.\n'.format(np.median(scn.snr)))
            print('\nSN#1 created.\n')

        print('Execution time: {:.2f} s. \n'.format(t7-t6))

        # Print a warning if the SNR of the brightest calibrator is < 40
        if np.median(calibrator_scans[0].snr) < 40:
            for pipeline_log in log_list:
                pipeline_log.write('\nWARNING: The brightest scan has a low SNR.\n')

            print('\nWARNING: The brightest scan has a low SNR.\n')
        
    # If there is an input calibrator
    if input_calibrator != 'NONE':
        ## Look for calibrator ##
        ## SNR fringe search ##
        disp.write_box(log_list, 'Calibrator search')
        
        #snr_fring(uvdata, refant)
        cali.snr_fring_only_fft(uvdata, refant)
        
        
        ## Get a list of scans ordered by SNR ##
        
        scan_list = cali.snr_scan_list_v2(uvdata, full_source_list)
        
        ## Get the scans for the input calibrator ## 
        calibrator_scans = [x for x in scan_list if x.name == input_calibrator]
        ## Order by SNR
        calibrator_scans.sort(key=lambda x: np.median(x.snr),\
                   reverse=True)
        
        calibrator_scans = [calibrator_scans[0]]
        t7 = time.time()

        for pipeline_log in log_list:
            pipeline_log.write('\nThe chosen scan for calibration is:\n')
            pipeline_log.write(str(calibrator_scans[0].name) + '\tSNR: ' \
                                + '{:.2f}.'.format(np.median(calibrator_scans[0].snr)))
            pipeline_log.write('\nSN#1 created.\n')
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t7-t6))

        print('\nThe chosen scan for calibration is:\n')
        print(str(calibrator_scans[0].name) + '\tSNR: ' \
                        + '{:.2f}.'.format(np.median(calibrator_scans[0].snr)))
        print('\nSN#1 created.\n')
        print('Execution time: {:.2f} s. \n'.format(t7-t6))


    ## Digital sampling correction ##
    disp.write_box(log_list, 'Digital sampling corrections')
    
    accr.sampling_correct(uvdata)
    t8 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nDigital sampling corrections applied! SN#2 and CL#5'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t8-t7))
    print('\nDigital sampling corrections applied! SN#2 and CL#5 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t8-t7))

    ## Instrumental phase correction ##
    disp.write_box(log_list, 'Instrumental phase corrections')
    
    if len(calibrator_scans) == 1:
        inst.manual_phasecal(uvdata, refant, calibrator_scans[0])
    else:
        inst.manual_phasecal_multi(uvdata, refant, calibrator_scans)
    t9 = time.time()
    
    for pipeline_log in log_list:
        pipeline_log.write('\nInstrumental phase correction applied using'\
                        + ' the calibrator(s). SN#3 and CL#6 created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t9-t8))
    print('\nInstrumental phase correction applied using the calibrator(s).'\
          + ' SN#3 and CL#6 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t9-t8))


    ## Bandpass correction ##
    disp.write_box(log_list, 'Bandpass correction')
    
    bpas.bp_correction(uvdata, refant, calibrator_scans)
    t10 = time.time()
    
    for pipeline_log in log_list:
        pipeline_log.write('\nBandpass correction applied! BP#1 created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t10-t9))
    print('\nBandpass correction applied! BP#1 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t10-t9))


    ## Correcting autocorrelations ##
    disp.write_box(log_list, 'Correcting autocorrelations')
    
    accr.correct_autocorr(uvdata)
    t11 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nAutocorrelations have been normalized! SN#4 and CL#7'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t11-t10))
    print('\nAutocorrelations have been normalized! SN#4 and CL#7 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t11-t10))


    ## Amplitude calibration ##
    disp.write_box(log_list, 'Amplitude calibration')

    # Check which antennas have GC, only calibrate those
    gc_antennas = [y['antenna_no'] for y in uvdata.table('GC',1)]
    gc_antennas = list(set(gc_antennas)) # Remove duplicates
    ampc.amp_cal(uvdata, gc_antennas)
    t12 = time.time()
    for pipeline_log in log_list:
        pipeline_log.write('\nAmplitude calibration applied! SN#5 and CL#8'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s.\n'.format(t12-t11))
    print('\nAmplitude calibration applied! SN#5 and CL#8 created.\n')
    print('Execution time: {:.2f} s.\n'.format(t12-t11))

    ## Fringe fit of the calibrator ##  
    # disp.write_box(log_list, 'Calibrator fringe fit')
    
    # frng.calib_fring_fit(uvdata, refant, calibrator_scans)
    # t13 = time.time()
    
    # for pipeline_log in log_list:
    #     pipeline_log.write('\nFringe fit applied to the calibrator! '\
    #                     + 'SN#6 and CL#9 created.\n')
    #     pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t11-t10))
    # print('\nFringe fit applied to the calibrator! SN#6 and CL#9 created.\n')
    # print('Execution time: {:.2f} s. \n'.format(t13-t12))
    
    ## Get optimal solution interval for each target
    disp.write_box(log_list, 'Target fringe fit')

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
            solint_list.append(opti.optimize_solint(uvdata, target, \
                                                    target_scans, refant))
            log_list[i].write('\nThe optimal solution interval for the target is '\
                        + str(solint_list[i]) + ' minutes. \n')
            print('\nThe optimal solution interval for ' + target + ' is ' \
                + str(solint_list[i]) + ' minutes. \n')
        else:
            phase_ref_scans = [x for x in scan_list if x.name == phase_ref[i]]
            solint_list.append(opti.optimize_solint(uvdata, phase_ref[i], \
                                                    phase_ref_scans, refant))
            log_list[i].write('\nThe optimal solution interval for the phase ' \
                            + 'calibrator is ' + str(solint_list[i]) + ' minutes. \n')
            print('\nThe optimal solution interval for the phase calibrator is ' \
                + str(solint_list[i]) + ' minutes. \n')
            
    t13 = time.time()
    
    for pipeline_log in log_list:    
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t13-t12)) 
    print('Execution time: {:.2f} s. \n'.format(t13-t12))

    ## Fringe fit of the target ##
   
    ## I NEED TO PRINT SOMETHING IF THERE ARE NO SOLUTIONS AT ALL ##
    for i, target in enumerate(target_list): 
        if phase_ref[i] == 'NONE':
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
        
                ratio = frng.assess_fringe_fit(uvdata, log_list[i], version = 6+i) 

            except RuntimeError:

                print("Fringe fit has failed.\n")

                log_list[i].write("Fringe fit has failed.\n")
                ratio = 0    
                
            # If the ratio is > 0.7, apply the solutions to a CL table

            if ratio >= 0.7:
                frng.fringe_clcal(uvdata, target, version = 9+i)

            # If the ratio is < 0.7 (arbitrary) repeat the fringe fit but averaging IFs

            if ratio < 0.7:

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
                
                    ratio_single = frng.assess_fringe_fit(uvdata, log_list[i], \
                                                          version = 6+i+1) 
                    
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
                    return()
    
                
                # If the new ratio is smaller or equal than the previous, 
                # then keep the previous

                if ratio_single <= ratio:
                    print("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    print("The multi-IF fringe fit will be applied.\n ")

                    log_list[i].write("New ratio of good/total solutions "\
                        + "is : {:.2f}.\n".format(ratio_single))
                    log_list[i].write("The multi-IF fringe fit will be applied.\n ")
                    frng.fringe_clcal(uvdata, target, version = 9+i)


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

            log_list[i].write('\nFringe fit corrections applied to the target! '\
                + 'SN#' + str(6+i) + ' and CL#' + str(9+i) \
                + ' created.\n')

            print('\nFringe fit corrections applied to ' + target + '! SN#' \
                + str(6+i) + ' and CL#' + str(9+i) + ' created.\n') 

        if phase_ref[i] != 'NONE':
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
        
                ratio = frng.assess_fringe_fit(uvdata, log_list[i], version = 6+i) 

            except RuntimeError:

                print("Fringe fit has failed.\n")

                log_list[i].write("Fringe fit has failed.\n")
                ratio = 0      


            # If the ratio is > 0.7, apply the solutions to a CL table

            if ratio >= 0.7:
                frng.fringe_phaseref_clcal(uvdata, target, version = 9+i)

            # If the ratio is < 0.7 (arbitrary) repeat the fringe fit but averaging IFs

            if ratio < 0.7:

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
                
                    ratio_single = frng.assess_fringe_fit(uvdata, log_list[i], \
                                                          version = 6+i+1) 
                    
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
                    return()
    
                
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

            log_list[i].write('\nFringe fit corrections applied to the target! '\
                + 'SN#' + str(6+i) + ' and CL#' + str(9+i) \
                + ' created.\n')

            print('\nFringe fit corrections applied to ' + target + '! SN#' \
                + str(6+i) + ' and CL#' + str(9+i) + ' created.\n') 

    t14 = time.time()
    
    ## Print the ratio of bad to good solutions ##
    for i, pipeline_log in enumerate(log_list):        
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t14-t13))  
    print('Execution time: {:.2f} s. \n'.format(t14-t13))

    ##  Export data ##
    disp.write_box(log_list, 'Exporting visibility data')

    expo.data_export(path_list, uvdata, target_list, flag_frac = flag_edge)
    expo.table_export(path_list, uvdata, target_list)
    for i, target in enumerate(target_list): 
        log_list[i].write('\n' + target + ' visibilites exported to ' + path_list[i] \
                          + '/' + target + '.uvfits\n')
        print('\n' + target + ' visibilites exported to ' + path_list[i] + '/' \
             + target + '.uvfits\n')
    for i, target in enumerate(target_list): 
        log_list[i].write('\n' + target + ' calibration tables exported to ' \
                          + path_list[i] + '/' + target + '.caltab.uvfits\n')
        print('\n' + target + ' calibration tables exported to ' + path_list[i] + '/' \
             + target + '.caltab.uvfits\n')

    ## PLOTS ##

    ## Plot visibilities as a function of frequency of target and calibrator ## 
    disp.write_box(log_list, 'Plotting visibilities')
    
    ## Uncalibrated ##
    for i, target in enumerate(target_list):
        plot.possm_plotter(path_list[i], uvdata, target, calibrator_scans, 1, \
                           bpver = 0, flag_edge=False)
    
        log_list[i].write('\nUncalibrated visibilities plotted in '  + path_list[i]  \
                           + '/' + target + '_CL1_POSSM.ps\n')
        print('\nUncalibrated visibilities plotted in '  + path_list[i] +  '/' \
                           + target + '_CL1_POSSM.ps\n')
        
    ## Calibrated ##
    for i, target in enumerate(target_list):
        plot.possm_plotter(path_list[i], uvdata, target, calibrator_scans, 9+i, \
                           bpver = 1)
        
        log_list[i].write('Calibrated visibilities plotted in ' + path_list[i] +  '/' \
                           + target + '_CL' + str(9+i) + '_POSSM.ps\n')
        print('Calibrated visibilities plotted in ' + path_list[i] +  '/' \
             + target + '_CL' + str(9+i) + '_POSSM.ps\n')
        
    ## Plot uv coverage ##
    for i, target in enumerate(target_list):
        plot.uvplt_plotter(path_list[i], uvdata, target)

        log_list[i].write('UV coverage of ' + target + ' plotted in ' \
                           + path_list[i] + '/' + target + '_UVPLT.ps\n')
        print('UV coverage of ' + target + ' plotted in ' + path_list[i] \
             + '/' + target + '_UVPLT.ps\n')
        
    ## Plot visibilities as a function of time of target## 
    for i, target in enumerate(target_list):
        plot.vplot_plotter(path_list[i], uvdata, target, 9+i)     
        
        log_list[i].write('Visibilities as a function of time of ' + target \
                           + ' plotted in ' + path_list[i]  + '/' + target \
                           + '_VPLOT.ps\n')
        print('Visibilities as a function of time of ' + target + ' plotted in ' \
              + path_list[i]  + '/' + target + '_VPLOT.ps\n')

    t15 = time.time()
    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t15-t14))
    print('Execution time: {:.2f} s. \n'.format(t15-t14))

    ## Total execution time ##
    tf = time.time()
    for pipeline_log  in log_list:
        pipeline_log.write('\nScript run time: '\
                         + '{:.2f} s. \n'.format(tf-t_i))
        pipeline_log.close()
    print('\nScript run time: {:.2f} s. \n'.format(tf-t_i))

def pipeline(input_dict):
    """Read the inputs, split multiple frequencies and calibrate the dataset

    :param input_dict: _description_
    :type input_dict: _type_
    """    
    # Read logo
    ascii_logo = open('./ascii_logo_string.txt', 'r').read()

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
            ## Select sources to load ##
            full_source_list = load.get_source_list(filepath_list, multifreq_id[2][ids])
            if load_all == False:
                calibs = load.find_calibrators(full_source_list)
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

            if multifreq_id[2][ids] > 1e10:
                klass_1 = str(multifreq_id[2][ids])[:2] + 'G'
            else:
                klass_1 = str(multifreq_id[2][ids])[:1] + 'G'

            # Define AIPS name
            hdul = fits.open(filepath_list[0])
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
                for filepath in filepath_list:
                    log_list[i].write(os.path.basename(filepath) + ' --- '\
                                        + '{:.2f} MB \n'.format\
                                        (os.path.getsize(filepath)/1024**2 ))

            ## START THE PIPELINE ##         
            calibrate(filepath_list, aips_name_short, sources, full_source_list, \
                        target_list, filename_list, log_list, path_list, \
                        disk_number, klass = klass_1, \
                        multi_id = True, selfreq = multifreq_id[2][ids]/1e6,\
                        default_refant = def_refant, input_calibrator = inp_cal, \
                        load_all = load_all, shift_coords = shifts, \
                        phase_ref = phase_ref, flag_edge = flag_edge)
            
        return() # STOP the pipeline. This needs to be tweaked.

    # If there are multiple IFs:   
    if multifreq_if[0] == True:
        
        klass_1 = multifreq_if[5] + 'G'
        klass_2 = multifreq_if[6] + 'G'

        ## FIRST FREQUENCY ##
        ## Select sources to load ##
        full_source_list = load.get_source_list(filepath_list, multifreq_if[7])
        if load_all == False:
            calibs = load.find_calibrators(full_source_list)
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

        # Define AIPS name
        hdul = fits.open(filepath_list[0])
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
            for filepath in filepath_list:
                log_list[i].write(os.path.basename(filepath) + ' --- '\
                                    + '{:.2f} MB \n'.format\
                                    (os.path.getsize(filepath)/1024**2 ))
        
        ## START THE PIPELINE ##
        calibrate(filepath_list, aips_name_short, sources, full_source_list, target_list, \
                filename_list, log_list, path_list, \
                disk_number, klass = klass_1,\
                bif = multifreq_if[1], eif = multifreq_if[2], \
                default_refant = def_refant, input_calibrator = inp_cal, \
                load_all = load_all, shift_coords = shifts, flag_edge = flag_edge, \
                phase_ref = phase_ref)
        

        ## SECOND FREQUENCY ##
        ## Select sources to load ##
        full_source_list = load.get_source_list(filepath_list, multifreq_if[8])
        if load_all == False:
            calibs = load.find_calibrators(full_source_list)
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
        
        # Define AIPS name
        hdul = fits.open(filepath_list[0])
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
            for filepath in filepath_list:
                log_list[i].write(os.path.basename(filepath) + ' --- '\
                                    + '{:.2f} MB \n'.format\
                                    (os.path.getsize(filepath)/1024**2 ))
            
        ## START THE PIPELINE ##  
        calibrate(filepath_list, aips_name_short, sources, full_source_list, target_list, \
                filename_list, log_list, path_list, \
                disk_number, klass = klass_2, \
                bif = multifreq_if[3], eif = multifreq_if[4], default_refant = def_refant, \
                input_calibrator = inp_cal, load_all = load_all, shift_coords = shifts,
                flag_edge = flag_edge, phase_ref = phase_ref)

        # End the pipeline
        return()

     # If there is only one frequency:  
    if multifreq_id[0] == False and multifreq_if[0] == False:
        
        klass_1 = multifreq_if[5] + 'G'
        
        ## Select sources to load ##
        full_source_list = load.get_source_list(filepath_list)
        if load_all == False:
            calibs = load.find_calibrators(full_source_list)
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
            filename_list[i] = name + '_' + klass_1
            path_list[i] = project_dir + '/' + filename_list[i]
            
            if os.path.exists(project_dir + '/' + filename_list[i]) == True:
                os.system('rm -rf ' + project_dir + '/' + filename_list[i])
            os.system('mkdir ' + project_dir + '/' + filename_list[i])

            log_list[i] = open(project_dir + '/' + filename_list[i] + '/' + name \
                        + '_pipeline_log.txt', 'w+')
            log_list[i].write(ascii_logo + '\n')
            for filepath in filepath_list:
                log_list[i].write(os.path.basename(filepath) + ' --- '\
                                    + '{:.2f} MB \n'.format\
                                    (os.path.getsize(filepath)/1024**2 ))
            
        ## START THE PIPELINE ##               
        calibrate(filepath_list, aips_name, sources, full_source_list, target_list, \
                filename_list, log_list, path_list, \
                disk_number, klass = klass_1, default_refant = def_refant, \
                input_calibrator = inp_cal, load_all = load_all, shift_coords = shifts,
                flag_edge = flag_edge, phase_ref = phase_ref)   