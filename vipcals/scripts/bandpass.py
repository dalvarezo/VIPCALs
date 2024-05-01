from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

import numpy as np
import os


def ddhhmmss(time):
    """Convert decimal dates into AIPS dd hh mm ss format.

    :param time: decimal date
    :type time: float
    :return: 1D array with day, hour, minute and second
    :rtype: ndarray
    """   
    total_seconds = int(time * 24 * 60 * 60)
    days, remainder = divmod(total_seconds, 24 * 60 * 60)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes, seconds = divmod(remainder, 60)
    return np.array([days,hours,minutes,seconds])
    

def bp_correction(data,refant, cal_scan):
    """Apply complex bandpass correction to the data.

    Generates BP#1

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param cal_scan: scan used for the calibration
    :type cal_scan: Scan object
    """    
    calib = cal_scan.name
    scan_time = cal_scan.time
    scan_time_interval = cal_scan.time_interval
    init_time = ddhhmmss(scan_time - 0.9*scan_time_interval/2)
    final_time = ddhhmmss(scan_time + 0.9*scan_time_interval/2)
    timer = [None] + init_time.tolist() + final_time.tolist()
    	
    bpass = AIPSTask('bpass')
    bpass.inname = data.name
    bpass.inclass = data.klass
    bpass.indisk = data.disk
    bpass.inseq = data.seq
    bpass.refant = refant    
    bpass.calsour = AIPSList([calib])
    bpass.timerang = timer
    bpass.docalib = 1
    bpass.solint = -1  # Whole timerange
    
    bpass.bpassprm[1:] = [0,0,0,0,0,0,0,0,0,0,0]  # Reset parameters
    bpass.bpassprm[5] = 1  # Not divide by channel 0
    bpass.bpassprm[9] = 1  # Interpolate over flagged channels
    bpass.bpassprm[10] = 6  # normalize amplitudes and zero average 
                            # phase using all channels in power, not
                            # voltage
    bpass.gainuse = 0
    bpass.outvers = 1
    bpass.msgkill = -4
    
    bpass.go()
        