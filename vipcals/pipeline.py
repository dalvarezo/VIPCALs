import os
import time 
import numpy as np
from datetime import datetime

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

from AIPSData import AIPSUVData


def pipeline(filepath, filename, sources, full_source_list, target,
             disk_number, pipeline_log, klass = '', seq = 1, bif = 0, eif = 0,\
             multi_id = False, selfreq = 0):
    
    ## Check if the filename is too long, and rename ##
    filename_short = filename
    if len(filename) > 12:
        name = filename.split('_')[0]
        suffix = filename.split('_')[1]
        size_name = 12 - (len(suffix) + 1)
        filename_short = name[:size_name] + '_' + suffix
        
    ## Check if the test file already exists and delete it ##
    
    uvdata = AIPSUVData(filename_short, klass, disk_number, seq)
    
    if uvdata.exists() == True:
        uvdata.zap()


    ## 1.- LOAD DATA ##
    disp.write_box(pipeline_log, 'Loading data')
    
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
        load.load_data(shortpath, filename_short, sources, disk_number, multi_id,\
        selfreq, klass = klass, bif = bif, eif = eif)
        t1 = time.time()   
        # IF load_data FAILS, THEN THE aux.uvfits FILE IS NOT REMOVED
        # I NEED TO CHECK AND REMOVE IT BEFOREHAND IF IT ALREADY EXISTS
        # Isn't it solved above? I'm not sure now
        # os.system('rm -f ' + shortpath) 
    else:
        ## Load the dataset ##
        t0 = time.time()
        load.load_data(filepath, filename_short, sources, disk_number, multi_id,\
        selfreq, klass = klass, bif = bif, eif = eif)
        t1 = time.time() 
 
    
    pipeline_log.write('\nData loaded! The loaded sources are ' + \
                       str(list(set(sources))) + '.\n')
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t1-t0))
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
    
    ## Check for CL/NX tables
    if [1, 'AIPS CL'] not in uvdata.tables or [1, 'AIPS NX'] not in \
        uvdata.tables:
        tabl.run_indxr(uvdata)
        print('\nINDXR was run, NX#1 and CL#1 were created.\n')
        
    ## Print scan information ##    
    # Remove the scanlist if it already exists
    # if os.path.exists('./' + filename + '/scansum.txt'):
    #     os.system('rm ' + './' + filename + '/scansum.txt')
    # Not necessary necause I remove the whole directory beforehand,
    # but I need to think again about it
    load.print_listr(uvdata, pipeline_log)

    ## Check for TY/GC/FG tables
    
    if ([1, 'AIPS TY'] not in uvdata.tables or [1, 'AIPS GC'] \
    not in uvdata.tables or [1, 'AIPS FG'] not in uvdata.tables):
        disp.write_box(pipeline_log, 'Loading external table information')
        pipeline_log.write('\n')
    
    if [1, 'AIPS TY'] not in uvdata.tables:
        tabl.load_ty_tables(uvdata, bif, eif, pipeline_log)

    if [1, 'AIPS GC'] not in uvdata.tables:
        tabl.load_gc_tables(uvdata, pipeline_log)
        
    if [1, 'AIPS FG'] not in uvdata.tables:
        tabl.load_fg_tables(uvdata, pipeline_log)

    ## If the time resolution is < 0.33s, average the dataset in time
    try:
        time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'][0])
    except TypeError: # Single IF datasets
        time_resol = float(uvdata.table('CQ', 1)[0]['time_avg'])
        
    if time_resol < 0.33:
        avgdata = AIPSUVData(filename_short, 'AVGT', disk_number, seq)
        if avgdata.exists() == True:
            avgdata.zap()
        tabl.time_aver(uvdata, time_resol, 2)
        uvdata = AIPSUVData(filename_short, 'AVGT', disk_number, seq)
        
        disp.write_box(pipeline_log, 'Data averaging')
        
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
        avgdata = AIPSUVData(filename_short, 'AVGF', disk_number, seq)
        if avgdata.exists() == True:
            avgdata.zap()
        ratio = no_chan/32    # NEED TO ADD A CHECK IN CASE THIS FAILS
        
        if time_resol >= 0.33: # = If it was not written before
            disp.write_box(pipeline_log, 'Data averaging')
        
        tabl.freq_aver(uvdata,ratio)
        uvdata = AIPSUVData(filename_short, 'AVGF', disk_number, seq)
        
        pipeline_log.write('\nThere were ' + str(no_chan) + ' channels per '+ \
                           'IF. It has been averaged to 32 channels.\n')
        print('\nThere were ' + str(no_chan) + ' channels per IF. It has '\
              'been averaged to 32 channels.\n')

    
    ## Smooth the TY table ##    
    
    disp.write_box(pipeline_log, 'Flagging system temperatures')
    
    tysm.ty_smooth(uvdata)
    
    original_tsys, flagged_tsys = tysm.assess_ty(uvdata)
    
    # Maybe this output could be written as a %, I just need to manually write
    # the case where 0 points are flagged
    
    pipeline_log.write('\nSystem temperatures clipped!. ' + str(flagged_tsys) \
                       + ' Tsys points out of a total of ' \
                       + str(original_tsys) + ' have been flagged. '\
                       + 'TY#2 created.\n')
     
    print('\nSystem temperatures clipped!. ' + str(flagged_tsys) \
          + ' Tsys points out of a total of ' \
          + str(original_tsys) + ' have been flagged. '\
          + 'TY#2 created.\n')
    
    
    t2 = time.time()  
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t2-t1))
    print('Execution time: {:.2f} s. \n'.format(t2-t1))

    ## Choose refant ##
    
    disp.write_box(pipeline_log, 'Reference antenna search')
    
    refant = rant.refant_choose(uvdata, sources, full_source_list, pipeline_log)
    t3=time.time()
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t3-t2))
    print('Execution time: {:.2f} s. \n'.format(t3-t2))

    ## Ionospheric correction ##
    
    disp.write_box(pipeline_log, 'Ionospheric corrections')
    
    YYYY = int(uvdata.header.date_obs[:4])
    MM = int(uvdata.header.date_obs[5:7])
    DD = int(uvdata.header.date_obs[8:])
    date_obs = datetime(YYYY, MM, DD)
    if date_obs > datetime(1998,6,1):
        iono.ionos_correct(uvdata)
        t4 = time.time()
        pipeline_log.write('\nIonospheric corrections applied! CL#2 created.'\
                           + '\n')
        pipeline_log.write('Execution time: {:.2f} s. \n'.format(t4-t3))
        print('\nIonospheric corrections applied! CL#2 created.\n')
        print('Execution time: {:.2f} s. \n'.format(t4-t3))
        os.system('rm -rf /tmp/jplg*')
    else:
        t4 = time.time()
        iono.tacop(uvdata, 'CL', 1, 2)
        pipeline_log.write('\nIonospheric corrections not applied! IONEX '\
                           + 'files are not available for observations '\
                           + 'older than June 1998. CL#2 will be copied '\
                           + 'from CL#1.\n')
        print('\nIonospheric corrections not applied! IONEX files are not '\
              + 'available for observations older than June 1998. CL#2 '\
              + 'will be copied from CL#1.\n')
        
    ## Earth orientation parameters correction ##
    
    disp.write_box(pipeline_log, 'Earth orientation parameters corrections')
    
    eopc.eop_correct(uvdata)
    t5 = time.time()
    pipeline_log.write('\nEarth orientation parameter corrections applied! '\
                       + 'CL#3 created.\n')
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t5-t4))
    print('\nEarth orientation parameter corrections applied! CL#3 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t5-t4))
    os.system('rm -rf /tmp/usno_finals.erp')

        ## Digital sampling correction ##
    
    disp.write_box(pipeline_log, 'Digital sampling corrections')
    
    accr.sampling_correct(uvdata)
    t6 = time.time()
    pipeline_log.write('\nDigital sampling corrections applied! SN#1 and CL#4'\
                       + ' created.\n')
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t6-t5))
    print('\nDigital sampling corrections applied! SN#1 and CL#4 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t6-t5))

    ## Amplitude calibration ##
    
    disp.write_box(pipeline_log, 'Amplitude calibration')
    
    ampc.amp_cal(uvdata, sources)
    t7 = time.time()
    pipeline_log.write('\nAmplitude calibration applied! SN#2 and CL#5'\
                       + ' created.\n')
    pipeline_log.write('Execution time: {:.2f} s.\n'.format(t7-t6))
    print('\nAmplitude calibration applied! SN#2 and CL#5 created.\n')
    print('Execution time: {:.2f} s.\n'.format(t7-t6))

    ## Parallatic angle correction ##
    
    disp.write_box(pipeline_log, 'Parallactic angle corrections')
    
    pang.pang_corr(uvdata)
    t8 = time.time()
    pipeline_log.write('\nParallactic angle corrections applied! CL#6'\
                       + ' created.\n')
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t8-t7))
    print('\nParallactic angle corrections applied! CL#6 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t8-t7))

    ## Look for calibrator ##
    ## SNR fringe search ##
    
    disp.write_box(pipeline_log, 'Calibrator search')
    
    #snr_fring(uvdata, refant)
    cali.snr_fring_only_fft(uvdata, refant)
    
    
    ## Get a list of scans ordered by SNR ##
    
    scan_list, optimal_scan_list = cali.snr_scan_list(uvdata, full_source_list, \
                                                      pipeline_log)
    t9 = time.time()
    
    ## Check if snr_scan_list() returned an error and, if so, end the pipeline
    if scan_list == 404:
        pipeline_log.write('\nNone of the scans reached a minimum SNR of ' \
                           + '5 and the dataset could not be automatically ' \
                           + 'calibrated.\nThe pipeline will stop now.\n')
            
        print('\nNone of the scans reached a minimum SNR of ' \
              + '5 and the dataset could not be automatically ' \
              + 'calibrated.\nThe pipeline will stop now.\n')
            
        return()
    
    cal_scan = optimal_scan_list[0]
    
    pipeline_log.write('\nThe brightest source in the data set is ' \
                       + str(cal_scan.name) + ' with median SNR:'\
                       + ' {:.2f}.'.format(np.median(cal_scan.snr)) \
                       + ' SN#3 created.\n')
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t9-t8))
    print('\nThe brightest source in the data set is '\
          + str(cal_scan.name) \
          + ' with median SNR: {:.2f}.'.format(np.median(cal_scan.snr)) \
          + ' SN#3 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t9-t8))

    ## Instrumental phase correction ##
    
    disp.write_box(pipeline_log, 'Instrumental phase corrections')
    
    #inst.pulse_phasecal(uvdata, refant, cal_scan)
    inst.manual_phasecal(uvdata, refant, cal_scan)
    t10 = time.time()
    
    pipeline_log.write('\nInstrumental phase correction applied using'\
                       + ' the calibrator. SN#4 and CL#7 created.\n')
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t10-t9))
    print('\nInstrumental phase correction applied using the calibrator.'\
          + ' SN#4 and CL#7 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t10-t9))

    ## Fringe fit of the calibrator ##
        
    disp.write_box(pipeline_log, 'Calibrator fringe fit')
    
    frng.calib_fring_fit(uvdata, refant, cal_scan)
    t11 = time.time()
    
    pipeline_log.write('\nFringe fit applied to the calibrator! '\
                       + 'SN#5 and CL#8 created.\n')
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t11-t10))
    print('\nFringe fit applied to the calibrator! SN#5 and CL#8 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t11-t10))

    ## Bandpass correction ##
    
    disp.write_box(pipeline_log, 'Bandpass correction')
    
    bpas.bp_correction(uvdata, refant, cal_scan)
    t12 = time.time()
    
    pipeline_log.write('\nBandpass correction applied! BP#1 created.\n')
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t12-t11))
    print('\nBandpass correction applied! BP#1 created.\n')
    print('Execution time: {:.2f} s. \n'.format(t12-t11))
    
    ## Get optimal solution interval
    
    disp.write_box(pipeline_log, 'Target fringe fit')
    
    target_optimal_scans = opti.get_optimal_scans(target, optimal_scan_list, \
                                                  full_source_list)
        
    solint = opti.optimize_solint(uvdata, target, target_optimal_scans, \
                                  refant)
    t13 = time.time()
    
    pipeline_log.write('\nThe optimal solution interval for the target is '\
                       + str(solint) + ' minutes. \n')
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t13-t12))
    print('\nThe optimal solution interval for the target is ' + str(solint) \
          + ' minutes. \n')
    print('Execution time: {:.2f} s. \n'.format(t13-t12))
    ## Fringe fit of the target ##
    
    ## I NEED TO PRINT SOMETHING IF THERE ARE NO SOLUTIONS AT ALL ##
    
    frng.target_fring_fit(uvdata, refant, target, solint=float(solint))
    t14 = time.time()
    
    pipeline_log.write('\nFringe fit applied to the target! '\
                        + 'SN#6 and CL#9 created.\n')
    print('\nFringe fit applied to the target! SN#6 and CL#9 created.\n')
    
    ## Print the ratio of bad to good solutions ##
    frng.assess_fringe_fit(uvdata, pipeline_log)
                     

    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t14-t13))  
    print('Execution time: {:.2f} s. \n'.format(t14-t13))
    
    ## Plot visibilities of target and calibrator ##
    
    disp.write_box(pipeline_log, 'Plotting visibilities')
    
    ## Uncalibrated ##
    plot.possm_plotter(filename, uvdata, target, cal_scan, \
                       gainuse = 1, bpver = 0)
    
    pipeline_log.write('\nUncalibrated visibilities plotted in /' + filename \
                        + '/CL1_possm.ps\n')
    print('\nUncalibrated visibilities plotted in /' + filename \
          + '/CL1_possm.ps\n')
    ## Calibrated ##
    plot.possm_plotter(filename, uvdata, target, cal_scan, \
                       gainuse = 9, bpver = 1)
    
    pipeline_log.write('Calibrated visibilities plotted in /' + filename \
                        + '/CL9_possm.ps\n')
    print('Calibrated visibilities plotted in /' + filename \
          + '/CL9_possm.ps\n')
    t15 = time.time()
    pipeline_log.write('Execution time: {:.2f} s. \n'.format(t15-t14))
    print('Execution time: {:.2f} s. \n'.format(t15-t14))
