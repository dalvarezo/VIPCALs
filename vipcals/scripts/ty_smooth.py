import numpy as np
import os

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

def tacop(data, ext, invers, outvers):
    """Copy one calibration table to another.

    Copies one AIPS calibration table from one version to another one.

    :param data: visibility data
    :type data: AIPSUVData
    :param ext: table extension
    :type ext: str
    :param invers: input version
    :type invers: int
    :param outvers: output version
    :type outvers: int
    """    
    tacop = AIPSTask('tacop')
    tacop.inname = data.name
    tacop.inclass = data.klass 
    tacop.indisk = data.disk
    tacop.inseq = data.seq
    
    tacop.outname = data.name
    tacop.outclass = data.klass 
    tacop.outdisk = data.disk
    tacop.outseq = data.seq
    
    tacop.inext = ext
    tacop.invers = invers
    tacop.outvers = outvers
    tacop.msgkill = -4
    
    tacop.go()
  
def ty_smooth(data, tmin = 0, tmax = 1000, time_interv = 15, max_dev = 250):
    """Smooth/filter system temperature tables.
    
    Flag TSys values below tmin and above tmax. Also values that
    deviate more than (max_dev) K from a mean value. This is done on a 
    per-source basis. 

    Flag also antennas with no TY or GC table entries.
    
    Creates TY#2

    :param data: visibility data
    :type data: AIPSUVData
    :param tmin: minimum TSys value allowed in K, defaults to 0
    :type tmin: float, optional
    :param tmax: maximum TSys value allowed in K, defaults to 1000
    :type tmax: float, optional
    :param time_interv:  smoothing time interval in minutes, defaults to 15
    :type time_interv: float, optional
    :param max_dev: maximum TSys deviation allowed from the mean value of each \
        source in K; defaults to 250
    :type max_dev: float, optional

    :return: list of ids of antennas with no system temperature information
    :rtype: list of int
    :return: list of ids of antennas with no gain curve information
    :rtype: list of int
    """    
    tysmo = AIPSTask('tysmo')
    tysmo.inname = data.name
    tysmo.inclass = data.klass
    tysmo.indisk = data.disk
    tysmo.inseq = data.seq
    tysmo.invers = 1
    tysmo.outvers = 2
    tysmo.inext = 'TY'
    tysmo.dobtween = 0    # <= 0 Smooth each source separately
    tysmo.aparm[1] = tmin
    tysmo.aparm[6] = tmax
    tysmo.cparm[1] = time_interv
    tysmo.cparm[6] = max_dev 
    tysmo.msgkill = -4
    
    tysmo.go()

    # Flag antennas with no Tsys or GC information

    all_antennas = []
    for a in data.table('AN',1):
         all_antennas.append(a['nosta'])

    antennas_w_tsys = []
    for t in data.table('TY', 2):
        antennas_w_tsys.append(t['antenna_no'])
    antennas_w_tsys = list(set(antennas_w_tsys))

    antennas_w_gc = [y['antenna_no'] for y in data.table('GC',1)]

    bad_antennas = [z for z in all_antennas if z  not in antennas_w_tsys or \
                    z not in antennas_w_gc]
    
    antennas_no_tsys = [x for x in all_antennas if x not in antennas_w_tsys]
    antennas_no_gc = [x for x in all_antennas if x not in antennas_w_gc]

    # Copy FG1 to FG2
    tacop(data, 'FG', 1, 2)
    
    # Apply antennas flags 
    if len(bad_antennas) > 0:
        uvflg = AIPSTask('uvflg')
        uvflg.inname = data.name
        uvflg.inclass = data.klass
        uvflg.indisk = data.disk
        uvflg.inseq = data.seq

        uvflg.antennas = AIPSList(bad_antennas)
        uvflg.outfgver = 2
        uvflg.reason = 'NO TSYS'
        uvflg.msgkill = -4

        uvflg.go()

    return(antennas_no_tsys, antennas_no_gc)
    
def ty_assess(data):
    """Evaluate how many TSys datapoints have been flagged in TY#2

    It computes the difference between the total number of tsys entries \
    in TY#1 and TY#2.

    :param data: visibility data
    :type data: AIPSUVData
    :return: number of points in TY#1, number of flagged points in TY#2
    :rtype: tuple of float
    """    
    ty1 = data.table('TY', 1)
    ty2 = data.table('TY', 2)
    
    # Count valid tsys measurements
    total_points_1 = 0
    for tsys in ty1:
        try: 
            for tsys_if in tsys['tsys_1']:
                if tsys_if != tsys['tant_1'][0]:
                    total_points_1 += 1
        except TypeError: # Single IF datasets
            if tsys['tsys_1'] != tsys['tant_1']:
                    total_points_1 +=1
                    
    total_points_2 = 0
    for tsys in ty2:
        try: 
            for tsys_if in tsys['tsys_1']:
                if tsys_if != tsys['tant_1'][0]:
                    total_points_2 += 1
        except TypeError: # Single IF datasets
            if tsys['tsys_1'] != tsys['tant_1']:
                    total_points_2 +=1
                    
    original_points = total_points_1
    flagged_points = total_points_1 - total_points_2
    
    return(original_points, flagged_points)