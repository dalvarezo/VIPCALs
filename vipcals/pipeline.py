import os
import time 
import numpy as np
from datetime import datetime

from astropy.coordinates import SkyCoord

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


def pipeline(filepath, aips_name, sources, full_source_list, target_list,
             disk_number, klass = '', seq = 1, bif = 0, eif = 0, \
             multi_id = False, selfreq = 0, default_refant = 'NONE', \
             input_calibrator = 'NONE', load_all = False, shift_coords = 'None'):
    """Main workflow of the pipeline 

    :param filepath: path to the original uvfits/idifits file
    :type filepath: str
    :param aips_name: name for the catalogue entry in AIPS
    :type aips_name: str
    :param sources: list with source names
    :type sources: list of str
    :param full_source_list: list containing all sources in the dataset
    :type full_source_list: list of Source objects
    :param target_list: target names
    :type target_list: list of str
    :param disk_number:disk number whithin AIPS
    :type disk_number: int
    :param klass: class name whithin AIPS; defaults to ‘’
    :type klass: str, optional
    :param seq:sequence number within AIPS; defaults to 1
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
                         objects,in case a phase shift was necessary; defaults to 'NONE'
    :type shift_coords: list of SkyCoord
    """    
    ## PIPELINE STARTS
    t_i = time.time()
    ## Define folder names ##
    filename_list = target_list.copy()
    log_list = target_list.copy()
    for i, name in enumerate(filename_list):
        filename_list[i] = name + '_' + klass
        
    ## Open log(s) ##
    # Pipeline log
    for i, name in enumerate(filename_list):
        if os.path.exists('./' + name) == True:
            os.system('rm -rf ./' + name) 
        os.system('mkdir ' + name)
        # Let's see how to manage this, this doesn't convince me
        log_list[i] = open('./' + name + '/' + name \
                            + '_pipeline_log.txt', 'w+')
        log_list[i].write(os.path.basename(filepath) + ' --- '\
                            + '{:.2f} MB \n'.format\
                            (os.path.getsize(filepath)/1024**2 ))
        
    # AIPS log is only opened for the first target, it will be copied once the pipeline 
    # ends
    load.open_log(filename_list[0])

    ## Check if the AIPS catalogue name is too long, and rename ##
    aips_name_short = aips_name
    if len(aips_name) > 12:
        name = aips_name.split('_')[0]
        suffix = aips_name.split('_')[1]
        size_name = 12 - (len(suffix) + 1)
        aips_name_short = name[:size_name] + '_' + suffix
        
    ## Check if the test file already exists and delete it ##
    
    uvdata = AIPSUVData(aips_name_short, klass, disk_number, seq)
    
    if uvdata.exists() == True:
        uvdata.zap()


    ## 1.- LOAD DATA ##
    disp.write_box(log_list, 'Loading data')
    
    ## Check if the filepath is > 46 characters
    if len(filepath.split('/')[-1]) > 46:
 
        # directory = '/'.join(filepath.split('/')[:-1])
        # This would be the ideal, to create the hard link in the same 
        # directory where the file is located. In gunmen I cannot do 
        # this, since I have no write permission in for example 
        # /data/pipeline_test_sample/felix/
        # To keep it simple, for now, the hard link is created always 
        # in /data/pipeline_test_sample
        
        directory = '/data/pipeline_test_sample'        

        ## Create hard link to a shorter path
        
        # Delete if it already exists
        if os.path.exists(directory + '/aux.uvfits'):
            os.system('rm ' + directory + '/aux.uvfits')
        
        os.system('ln ' + filepath + ' ' + directory + '/aux.uvfits')
        shortpath = directory + '/aux.uvfits'
        
        ## Load the dataset ##
        t0 = time.time()
        load.load_data(shortpath, aips_name_short, sources, disk_number, multi_id,\
        selfreq, klass = klass, bif = bif, eif = eif, l_a = load_all)
        t1 = time.time()   
        # IF load_data FAILS, THEN THE aux.uvfits FILE IS NOT REMOVED
        # I NEED TO CHECK AND REMOVE IT BEFOREHAND IF IT ALREADY EXISTS
        # Isn't it solved above? I'm not sure now
        # os.system('rm -f ' + shortpath) 
    else:
        ## Load the dataset ##
        t0 = time.time()
        load.load_data(filepath, aips_name_short, sources, disk_number, multi_id,\
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
        tabl.remove_ascii_antname(uvdata, filepath)
        tabl.remove_ascii_poltype(uvdata)
        print('\nAN Table was modified to correct for padding in entries.\n')

    ## Check for order
    if uvdata.header['sortord'] != 'TB':
        tabl.tborder(uvdata, pipeline_log)
        for pipeline_log in log_list:
            pipeline_log.write('\nData was not in TB order. It has been reorder using ' \
                               + 'the UVSRT task\n')
        print('\nData was not in TB order. It has been reorder using ' \
              + 'the UVSRT task\n')
    
    ## Check for CL/NX tables
    if [1, 'AIPS CL'] not in uvdata.tables or [1, 'AIPS NX'] not in \
        uvdata.tables:
        tabl.run_indxr(uvdata)
        print('\nINDXR was run, NX#1 and CL#1 were created.\n')
        
    for pipeline_log in log_list:
        pipeline_log.write('\nScan information printed in /scansum.txt \n')
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
                pipeline_log.write('\nSystem temperatures were not available in the file, '\
                                    + 'they have been retrieved from ' + good_url + '\n')
            pipeline_log.write('TY#1 created.\n')

        # Move the temperature file to the target folders
        for name in filename_list:
            os.system('cp ./tsys.vlba ./' + name + '/flags.vlba')
    
        # And delete the files from the main directory
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
        for name in filename_list:
            os.system('cp ./gaincurves.vlba ./' + name + '/flags.vlba')
    
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
        for name in filename_list:
            os.system('cp ./flags.vlba ./' + name + '/flags.vlba')
    
        # And delete the files from the main directory
        os.system('rm ./tables*')
        os.system('rm ./flags.vlba')

        print('\nFlag information was not available in the file, it ' \
               + 'has been retrieved from online.\n')
        print('FG#1 created.\n')

    if missing_tables == True:
        t1 = time.time()
        for pipeline_log in log_list:
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t1-t_i_table))

    ## If the time resolution is < 0.33s, average the dataset in time
    try:
        time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'][0])
    except TypeError: # Single IF datasets
        time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'])
        
    if time_resol < 0.33:
        avgdata = AIPSUVData(aips_name_short, 'AVGT', disk_number, seq)
        if avgdata.exists() == True:
            avgdata.zap()
        tabl.time_aver(uvdata, time_resol, 2)
        uvdata = AIPSUVData(aips_name_short, 'AVGT', disk_number, seq)

        disp.write_box(log_list, 'Data averaging')
        for pipeline_log in log_list:
            pipeline_log.write('\nThe time resolution was ' \
                            + '{:.2f}'.format(time_resol) \
                            + 's. It has been averaged to 2s.\n')
        print('\nThe time resolution was {:.2f}'.format(time_resol) \
            + 's. It has been averaged to 2s.\n')
        
            
    ## If there are more than 128 channels, average the dataset in frequency
    try:
        no_chan = int(uvdata.table('CQ', 1)[0]['no_chan'][0])
    except TypeError: # Single IF datasets
        no_chan = int(uvdata.table('CQ', 1)[0]['no_chan'])
        
    if no_chan > 128:
        avgdata = AIPSUVData(aips_name_short, 'AVGF', disk_number, seq)
        if avgdata.exists() == True:
            avgdata.zap()
        ratio = no_chan/32    # NEED TO ADD A CHECK IN CASE THIS FAILS
        
        if time_resol >= 0.33: # = If it was not written before
            disp.write_box(log_list, 'Data averaging')
        
        tabl.freq_aver(uvdata,ratio)
        uvdata = AIPSUVData(aips_name_short, 'AVGF', disk_number, seq)
        for pipeline_log in log_list:
            pipeline_log.write('\nThere were ' + str(no_chan) + ' channels per '+ \
                            'IF. It has been averaged to 32 channels.\n')
        print('\nThere were ' + str(no_chan) + ' channels per IF. It has '\
              'been averaged to 32 channels.\n')

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


    ## Print scan information ##    
    # Remove the scanlist if it already exists
    # if os.path.exists('./' + filename + '/scansum.txt'):
    #     os.system('rm ' + './' + filename + '/scansum.txt')
    # Not necessary necause I remove the whole directory beforehand,
    # but I need to think again about it
    load.print_listr(uvdata, filename_list)
    ## Smooth the TY table ##    
    
    disp.write_box(log_list, 'Flagging system temperatures')
    
    tysm.ty_smooth(uvdata)
    
    original_tsys, flagged_tsys = tysm.ty_assess(uvdata)
    
    # Maybe this output could be written as a %, I just need to manually write
    # the case where 0 points are flagged
    for pipeline_log in log_list:
        pipeline_log.write('\nSystem temperatures clipped!. ' + str(flagged_tsys) \
                        + ' Tsys points out of a total of ' \
                        + str(original_tsys) + ' have been flagged. '\
                        + 'TY#2 created.\n')
     
    print('\nSystem temperatures clipped!. ' + str(flagged_tsys) \
          + ' Tsys points out of a total of ' \
          + str(original_tsys) + ' have been flagged. '\
          + 'TY#2 created.\n')
    
    
    t2 = time.time()  

    for pipeline_log in log_list:
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t2-t1))
    print('Execution time: {:.2f} s. \n'.format(t2-t1))

    ## Choose refant ##
    disp.write_box(log_list, 'Reference antenna search')
    
    if default_refant == 'NONE':
        refant = rant.refant_choose_snr(uvdata, sources, target_list, full_source_list, \
                                        log_list)
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

    ## Digital sampling correction ##
    disp.write_box(log_list, 'Digital sampling corrections')
    
    accr.sampling_correct(uvdata)
    t6 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nDigital sampling corrections applied! SN#1 and CL#4'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t6-t5))
    print('\nDigital sampling corrections applied! SN#1 and CL#4 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t6-t5))

    ## Amplitude calibration ##
    disp.write_box(log_list, 'Amplitude calibration')
    
    ampc.amp_cal(uvdata)
    t7 = time.time()
    for pipeline_log in log_list:
        pipeline_log.write('\nAmplitude calibration applied! SN#2 and CL#5'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s.\n'.format(t7-t6))
    print('\nAmplitude calibration applied! SN#2 and CL#5 created.\n')
    print('Execution time: {:.2f} s.\n'.format(t7-t6))

    ## Parallatic angle correction ##
    disp.write_box(log_list, 'Parallactic angle corrections')
    
    pang.pang_corr(uvdata)
    t8 = time.time()

    for pipeline_log in log_list:
        pipeline_log.write('\nParallactic angle corrections applied! CL#6'\
                        + ' created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t8-t7))
    print('\nParallactic angle corrections applied! CL#6 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t8-t7))

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

        t9 = time.time()

        for pipeline_log in log_list:
            if len(calibrator_scans) == 1:
                pipeline_log.write('\nThe chosen scan for calibration is:\n')
                pipeline_log.write(str(calibrator_scans[0].name) + '\tSNR: ' \
                                   + '{:.2f}.'.format(np.median(calibrator_scans[0].snr)))
                pipeline_log.write('\nSN#3 created.\n')

            else:
                pipeline_log.write('\nThe chosen scans for calibration are:\n')
                for scn in calibrator_scans:    
                    pipeline_log.write(str(scn.name) + '\tSNR: ' \
                                      + '{:.2f}.\n'.format(np.median(scn.snr)))
                pipeline_log.write('\nSN#3 created.\n')

            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t9-t8))

   
        if len(calibrator_scans) == 1:
            print('\nThe chosen scan for calibration is:\n')
            print(str(calibrator_scans[0].name) + '\tSNR: ' \
                            + '{:.2f}.'.format(np.median(calibrator_scans[0].snr)))
            print('\nSN#3 created.\n')

        else:
            print('\nThe chosen scans for calibration are:\n')
            for scn in calibrator_scans:    
                print(str(scn.name) + '\tSNR: {:.2f}.\n'.format(np.median(scn.snr)))
            print('\nSN#3 created.\n')

        print('Execution time: {:.2f} s. \n'.format(t9-t8))

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
        t9 = time.time()

        for pipeline_log in log_list:
            pipeline_log.write('\nThe chosen scan for calibration is:\n')
            pipeline_log.write(str(calibrator_scans[0].name) + '\tSNR: ' \
                                + '{:.2f}.'.format(np.median(calibrator_scans[0].snr)))
            pipeline_log.write('\nSN#3 created.\n')
            pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t9-t8))

        print('\nThe chosen scan for calibration is:\n')
        print(str(calibrator_scans[0].name) + '\tSNR: ' \
                        + '{:.2f}.'.format(np.median(calibrator_scans[0].snr)))
        print('\nSN#3 created.\n')
        print('Execution time: {:.2f} s. \n'.format(t9-t8))


    ## Instrumental phase correction ##
    disp.write_box(log_list, 'Instrumental phase corrections')
    
    if len(calibrator_scans) == 1:
        inst.manual_phasecal(uvdata, refant, calibrator_scans[0])
    else:
        inst.manual_phasecal_multi(uvdata, refant, calibrator_scans)
    t10 = time.time()
    
    for pipeline_log in log_list:
        pipeline_log.write('\nInstrumental phase correction applied using'\
                        + ' the calibrator(s). SN#4 and CL#7 created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t10-t9))
    print('\nInstrumental phase correction applied using the calibrator(s).'\
          + ' SN#4 and CL#7 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t10-t9))

    ## Fringe fit of the calibrator ##  
    disp.write_box(log_list, 'Calibrator fringe fit')
    
    frng.calib_fring_fit(uvdata, refant, calibrator_scans)
    t11 = time.time()
    
    for pipeline_log in log_list:
        pipeline_log.write('\nFringe fit applied to the calibrator! '\
                        + 'SN#5 and CL#8 created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t11-t10))
    print('\nFringe fit applied to the calibrator! SN#5 and CL#8 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t11-t10))

    ## Bandpass correction ##
    disp.write_box(log_list, 'Bandpass correction')
    
    bpas.bp_correction(uvdata, refant, calibrator_scans)
    t12 = time.time()
    
    for pipeline_log in log_list:
        pipeline_log.write('\nBandpass correction applied! BP#1 created.\n')
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t12-t11))
    print('\nBandpass correction applied! BP#1 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t12-t11))
    
    ## Get optimal solution interval for each target
    disp.write_box(log_list, 'Target fringe fit')
    
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
        target_scans = [x for x in scan_list if x.name == target]

        #else:
        solint_list.append(opti.optimize_solint(uvdata, target, \
                                                target_scans, refant))
        log_list[i].write('\nThe optimal solution interval for the target is '\
                    + str(solint_list[i]) + ' minutes. \n')
        print('\nThe optimal solution interval for ' + target + ' is ' \
            + str(solint_list[i]) + ' minutes. \n')
            
    t13 = time.time()
    
    for pipeline_log in log_list:    
        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t13-t12)) 
    print('Execution time: {:.2f} s. \n'.format(t13-t12))

    ## Fringe fit of the target ##
    
    ## I NEED TO PRINT SOMETHING IF THERE ARE NO SOLUTIONS AT ALL ##
    for i, target in enumerate(target_list): 
        tfring_params = frng.target_fring_fit(uvdata, refant, target, \
                                              solint=float(solint_list[i]), version = 9+i)
        
        log_list[i].write('\nFringe search performed on ' + target + '. Windows for ' \
                         + 'the search were ' + tfring_params[1] + ' ns and ' \
                         + tfring_params[2] + ' mHz.\n')
        
        log_list[i].write('\nFringe fit corrections applied to the target! '\
                        + 'SN#' + str(6+i) + ' and CL#' + str(9+i) + ' created.\n')
        
        print('\nFringe search performed on ' + target + '. Windows for ' \
             + 'the search were ' + tfring_params[1] + ' ns and ' \
             + tfring_params[2] + ' mHz.\n')
        
        print('\nFringe fit corrections applied to ' + target + '! SN#' + str(6+i) + \
              ' and CL#' + str(9+i) + ' created.\n')   
    t14 = time.time()
    
    ## Print the ratio of bad to good solutions ##
    for i, pipeline_log in enumerate(log_list):
        frng.assess_fringe_fit(uvdata, pipeline_log, version = 6+i)               

        pipeline_log.write('\nExecution time: {:.2f} s. \n'.format(t14-t13))  
    print('Execution time: {:.2f} s. \n'.format(t14-t13))

    ##  Export data ##
    disp.write_box(log_list, 'Exporting visibility data')

    expo.data_export(filename_list, uvdata, target_list)
    for i, target in enumerate(target_list): 
        log_list[i].write('\n' + target + ' visibilites exported to ' + target \
                         + '.uvfits\n')
        print('\n' + target + ' visibilites exported to ' + target + '.uvfits\n')

    ## PLOTS ##

    ## Plot visibilities as a function of frequency of target and calibrator ## 
    disp.write_box(log_list, 'Plotting visibilities')
    
        ## Uncalibrated ##
    for i, target in enumerate(target_list):
        plot.possm_plotter(filename_list[i], uvdata, target, calibrator_scans, 1, \
                           bpver = 0, flag_edge=False)
    
        log_list[i].write('\nUncalibrated visibilities plotted in /' + filename_list[i] \
                        + '/CL1_possm.ps\n')
        print('\nUncalibrated visibilities plotted in /' + filename_list[i] \
            + '/CL1_possm.ps\n')
        
        ## Calibrated ##
    for i, target in enumerate(target_list):
        plot.possm_plotter(filename_list[i], uvdata, target, calibrator_scans, 9+i, \
                           bpver = 1)
        
        pipeline_log.write('Calibrated visibilities plotted in /' + filename_list[i] \
                            + '/CL' + str(9+i) + '_possm.ps\n')
        print('Calibrated visibilities plotted in /' + filename_list[i] \
            + '/CL' + str(9+i) + '_possm.ps\n')
        
    ## Plot uv coverage ##
    for i, target in enumerate(target_list):
        plot.uvplt_plotter(filename_list[i], uvdata, target)

        pipeline_log.write('UV coverage plotted in /' + filename_list[i] \
                          + '/' + target + '_UVPLT.ps\n')
        print('UV coverage plotted in /' + filename_list[i] \
             + '/' + target + '_UVPLT.ps\n')
        
    ## Plot visibilities as a function of time of target## 
    for i, target in enumerate(target_list):
        plot.vplot_plotter(filename_list[i], uvdata, target, 9+i)     
        
        pipeline_log.write('Visibilities as a function of time plotted in ' \
                           + '/' + filename_list[i]  + '/' + target + '_VPLOT.ps\n')
        print('Visibilities as a function of time plotted in ' \
             + '/' + filename_list[i]  + '/' + target + '_VPLOT.ps\n')

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
