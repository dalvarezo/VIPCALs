from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

import numpy as np
import os

def ddhhmmss(time):
    """Convert decimal dates into AIPS dd hh mm ss format."""
    total_seconds = int(time * 24 * 60 * 60)
    days, remainder = divmod(total_seconds, 24 * 60 * 60)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes, seconds = divmod(remainder, 60)
    return np.array([days,hours,minutes,seconds])


def get_calib(number, scan_list, full_source_list):
    """Gets information of the calibrator from the scan list."""
    scan_time = scan_list[number].time
    scan_time_interval = scan_list[number].time_interval
    init_time = ddhhmmss(scan_time - 0.9*scan_time_interval/2)
    final_time = ddhhmmss(scan_time + 0.9*scan_time_interval/2)
    timerang = [None] + init_time.tolist() + final_time.tolist()
    
    source_id = scan_list[number].id
    source_name = next(source for source in full_source_list \
                       if source.id == source_id).name
                       
    return(str(source_name), timerang)
    

def possm_plotter(filename, data, target, cal_scan, \
                  gainuse = 1, bpver = 0, number = 0 ):
    """Plot visibilities as a function of frequency to a PostScript file."""
    
    calib = cal_scan.name
    
    possm = AIPSTask('possm')
    possm.inname = data.name
    possm.inclass = data.klass
    possm.indisk = data.disk
    possm.inseq = data.seq

    possm.sources = AIPSList([calib, target])
    possm.stokes = 'RRLL'
    possm.solint = -1
    
    possm.docalib = 1
    possm.gainuse = gainuse
    if bpver > 0:
        possm.doband = 1
        possm.bpver = bpver
    
    possm.aparm = AIPSList([1, 1, 0, 0, -180, 180, 0, 0, 1, 0])
    possm.nplots = 9
    
    possm.dotv = -1
    possm.msgkill = -4
    
    possm.go()
    
    # Get the maximum plot number from POSSM
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
    
    lwpla = AIPSTask('lwpla')
    lwpla.inname = data.name
    lwpla.inclass = data.klass
    lwpla.indisk = data.disk
    lwpla.inseq = data.seq

    lwpla.plver = 1
    lwpla.invers = max_plot
    
    lwpla.dparm = AIPSList([0, 0, 0, 0, 0, 4, 31, 7, 0 ])
    lwpla.outfile = './' + filename + '/CL' + str(gainuse) + '_possm.ps'
    
    lwpla.msgkill = -4
    
    lwpla.go()
    
    # Clean all plots
    data.zap_table('PL', -1)