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
    

def possm_plotter(filename, data, target, cal_scan, \
                  gainuse, bpver = 0):
    """Plot visibilities as a function of frequency to a PostScript file.

    :param filename: name of the output folder 
    :type filename: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target: science target name
    :type target: str
    :param cal_scan: scan used for the calibration
    :type cal_scan: Scan object
    :param gainuse: CL version to apply
    :type gainuse: int
    :param bpver: BP table version to use, if = 0 then don't correct for bandpass, \
    defaults to 0
    :type bpver: int, optional
    """    
    """"""
    
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