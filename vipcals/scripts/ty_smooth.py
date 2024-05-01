import numpy as np
import os

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

  
def ty_smooth(data, tmin = 0, tmax = 1000, time_interv = 15, max_dev = 250):
    """Smooth/filter system temperature tables.
    
    Flag TSys values below tmin and above tmax. Also values that
    deviate more than (max_dev) K from a mean value. This is done on a 
    per-source basis. 
    
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
        source in K, defaults to 250
    :type max_dev: float, optional
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