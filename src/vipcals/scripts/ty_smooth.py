import numpy as np
import os

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

  
def ty_smooth(data, tmin = 0, tmax = 1000, time_interv = 15, max_dev = 250):
    """Smooth/filter system temperature tables.
    
    Flag TSys values below tmin and above tmax. Also values that
    deviate more than max_dev K from a mean value. This is done on a 
    per-source basis. It creates TY#2
    
    Arguments:
    ---------
    
    data: (AIPSUVData)
        visibility data
    
    tmin: (float)
        minimum TSys value allowed (K)
    
    tmax: (float)
        maximum TSys value allowed (K)
    
    time_interv: (float)
        smoothing time interval (minutes)
    
    max_dev: (float)
        maximum TSys deviation allowed from the mean value of each 
        source (K)
        
    Returns:
    --------
    TY#2 (AIPS Table)
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
    
    
def assess_ty(data):
    """Evaluate how many TSys datapoints have been flagged in TY#2
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