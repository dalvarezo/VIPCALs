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
    

def possm_plotter(filepath, data, target, cal_scans, \
                  gainuse, bpver = 0, flag_edge = True, flag_frac = 0.1):
    """Plot visibilities as a function of frequency to a PostScript file.

    :param filepath: path of the output directory 
    :type filepath: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target: science target name
    :type target: str
    :param cal_scans: list of scans used for the calibration
    :type cal_scans: list of Scan object
    :param gainuse: CL version to apply
    :type gainuse: int
    :param bpver: BP table version to use, if = 0 then don't correct for bandpass, \
                  defaults to 0
    :type bpver: int, optional
    :param flag_edge: flag edge channels; defaults to True
    :type flag_edge: bool, optional
    :param flag_frac: number of edge channels to flag, either a percentage (if < 1) \
                      or an integer number of channels (if >= 1); defaults to 0.1
    :type flag_frac: float, optional
    """    
    
    calib_names = [x.name for x in cal_scans]
    
    possm = AIPSTask('possm')
    possm.inname = data.name
    possm.inclass = data.klass
    possm.indisk = data.disk
    possm.inseq = data.seq

    possm.sources = AIPSList(calib_names + [target])
    possm.stokes = 'RRLL'
    possm.solint = -1
    
    possm.docalib = 1
    possm.gainuse = gainuse
    if bpver > 0:
        possm.doband = 1
        possm.bpver = bpver


    try:
        no_channels = int(data.table('FQ',1)[0]['total_bandwidth'][0] / \
                      data.table('FQ',1)[0]['ch_width'][0])
    except TypeError:   # Single IF datasets
        no_channels = int(data.table('FQ',1)[0]['total_bandwidth'] / \
                      data.table('FQ',1)[0]['ch_width'])
        
    if flag_edge == True and flag_frac < 1:
        flag_chann = int(flag_frac * no_channels)
    if flag_edge == True and flag_frac >= 1:
        if type(flag_frac) != int:
            flag_chann = 0
            # I NEED TO PRINT AN ERROR MESSAGE
        else:
            flag_chann = flag_frac
    if flag_edge == False:
        flag_chann = 0
    
    possm.bchan = flag_chann + 1
    possm.echan = no_channels - flag_chann

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
    lwpla.outfile = filepath +  '/' + target + '_CL' + str(gainuse) + '_POSSM.ps'
    
    lwpla.msgkill = -4
    
    lwpla.go()
    
    # Clean all plots
    data.zap_table('PL', -1)


def uvplt_plotter(filepath, data, target, solint = 0.17):
    """Plot UV coverage for a source to a PostScript file.

    :param filepath: path of the output directory 
    :type filepath: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target: science target name
    :type target: str
    :param solint: time averaging interval in minutes; defaults to 0.17
    :type solint: float, optional
    """    
    uvplt = AIPSTask('uvplt')
    uvplt.inname = data.name
    uvplt.inclass = data.klass
    uvplt.indisk = data.disk
    uvplt.inseq = data.seq

    uvplt.sources = AIPSList([target])
    uvplt.docalib = 1
    uvplt.gainuse = 0

    uvplt.bparm = AIPSList([6, 7, 0, 0, 0, 0, 0, 0, 0, 0])  # (u,v) for x-  and y- axes
    uvplt.solint = solint  # Default is 0.17 min (10 seconds)

    uvplt.do3color = -1  # Black and white plot
    uvplt.dotv = -1
    uvplt.msgkill = -4
    
    uvplt.go()

    # Export the plot

    lwpla = AIPSTask('lwpla')
    lwpla.inname = data.name
    lwpla.inclass = data.klass
    lwpla.indisk = data.disk
    lwpla.inseq = data.seq

    lwpla.plver = 1
    lwpla.invers = 1
    
    lwpla.dparm = AIPSList([0, 0, 0, 0, 0, 4, 31, 7, 0 ])
    lwpla.outfile = filepath + '/' + target + '_UVPLT.ps'
    
    lwpla.msgkill = -4
    
    lwpla.go()
    
    # Clean all plots
    data.zap_table('PL', -1)


def vplot_plotter(filepath, data, target, gainuse, bpver = 0, avgif = 1, avgchan = 1, \
                  solint = 0.17):
    """Plot visibilities as a function of time to a PostScript file.

    :param filepath: path of the output directory 
    :type filepath: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target: science target name
    :type target: str
    :param gainuse: CL version to apply
    :type gainuse: int
    :param bpver: BP table version to use, if = 0 then don't correct for bandpass; \
                  defaults to 0
    :type bpver: int, optional
    :param avgif: average the data in IFs, 0 => False, 1 => True; defaults to 1
    :type avgif: int, optional
    :param avgchan: average the data in channels, 0 => False, 1 => True; defaults to 1
    :type avgchan: int, optional
    :param solint: time averaging interval in minutes; defaults to 0.17
    :type solint: float, optional
    """    
    vplot = AIPSTask('vplot')
    vplot.inname = data.name
    vplot.inclass = data.klass
    vplot.indisk = data.disk
    vplot.inseq = data.seq

    vplot.sources = AIPSList([target])
    vplot.avgchan = 1
    vplot.avgif = 1
    vplot.solint = solint

    vplot.docalib = 1
    vplot.gainuse = gainuse
    if bpver > 0:
        vplot.doband = 1
        vplot.bpver = bpver

    vplot.bparm = AIPSList([12, -1, 0, 0, 0, 0, 0, 0, 0, 0])  
                  # (IAT hours, Amp & Phase) for x-  and y- axes
    vplot.nplots = 2

    vplot.dotv = -1
    vplot.msgkill = -4
    
    vplot.go()

    # Get the maximum plot file number 
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
    lwpla.outfile = filepath + '/' + target + '_VPLOT.ps'
    
    lwpla.msgkill = -4
    
    lwpla.go()
    
    # Clean all plots
    data.zap_table('PL', -1)