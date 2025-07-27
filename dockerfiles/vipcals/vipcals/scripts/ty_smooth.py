from scripts.helper import tacop

from AIPSTask import AIPSTask, AIPSList

AIPSTask.msgkill = -8
  
def ty_smooth(data, tmin = 0, tmax = 1000, time_interv = 15, max_dev = 250):
    """Smooth/filter system temperature tables.
    
    Flag TSys values below tmin and above tmax using the TYSMO task in AIPS. Also 
    flag values that deviate more than (max_dev) K from a mean value. This is done on a 
    per-source basis. 

    Flag also antennas with no TY or GC table entries using the UVFLG task.
    
    Creates TY#2

    :param data: visibility data
    :type data: AIPSUVData
    :param tmin: minimum TSys value allowed in K; defaults to 0
    :type tmin: float, optional
    :param tmax: maximum TSys value allowed in K; defaults to 1000
    :type tmax: float, optional
    :param time_interv:  smoothing time interval in minutes; defaults to 15
    :type time_interv: float, optional
    :param max_dev: maximum TSys deviation allowed from the mean value of each 
        source in K; defaults to 250
    :type max_dev: float, optional

    :return: list of ids of antennas with no system temperature information, 
             list of ids of antennas with no gain curve information
    :rtype: list of int, list of int
    """    
    tysmo = AIPSTask('tysmo')
    tysmo.inname = data.name
    tysmo.inclass = data.klass
    tysmo.indisk = data.disk
    tysmo.inseq = data.seq
    tysmo.invers = 1
    tysmo.outvers = 2
    tysmo.flagver = -1   # Don't apply flags. Empty flag tables can make the task 
                         # malfunction.
    tysmo.inext = 'TY'
    tysmo.dobtween = 0    # 0 Smooth each source separately
    tysmo.aparm[1] = tmin
    tysmo.aparm[6] = tmax
    tysmo.cparm[1] = time_interv
    tysmo.cparm[6] = max_dev 
    
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
        uvflg.reason = 'NO TSYS/GC'

        uvflg.go()

    return(antennas_no_tsys, antennas_no_gc)
    
def ty_assess(data):
    """Evaluate how many TSys datapoints have been flagged in TY#2.

    It computes the difference between the total number of tsys entries in TY#1 and TY#2.

    :param data: visibility data
    :type data: AIPSUVData
    :return: number of points in TY#1, number of flagged points in TY#2, dictionary with 
        these values per antenna
    :rtype: float, float, dict
    """    
    ty1 = data.table('TY', 1)
    ty2 = data.table('TY', 2)
    ant_ids = [x.nosta for x in data.table('AN', 1)]
    ant_dict = {}
    for id in ant_ids:
        ant_dict[id] = [0,0]
    
    # Count valid tsys measurements
    total_points_1 = 0
    for tsys in ty1:
        try: 
            for tsys_if in tsys['tsys_1']:
                if tsys_if != tsys['tant_1'][0]:
                    total_points_1 += 1
                    ant_dict[tsys['antenna_no']][1] += 1
        except TypeError: # Single IF datasets
            if tsys['tsys_1'] != tsys['tant_1']:
                    total_points_1 +=1
                    ant_dict[tsys['antenna_no']][1] += 1
                    
    total_points_2 = 0
    for tsys in ty2:
        try: 
            for tsys_if in tsys['tsys_1']:
                if tsys_if != tsys['tant_1'][0]:
                    total_points_2 += 1
                    ant_dict[tsys['antenna_no']][0] += 1
        except TypeError: # Single IF datasets
            if tsys['tsys_1'] != tsys['tant_1']:
                    total_points_2 +=1
                    ant_dict[tsys['antenna_no']][0] += 1
                    
    original_points = total_points_1
    flagged_points = total_points_1 - total_points_2

    tsys_dict= {}
    for key in ant_dict:
        name = [x.anname for x in data.table('AN', 1) if x.nosta == key][0]
        tsys_dict[key] = (name, ant_dict[key][0], ant_dict[key][1])
    
    return(original_points, flagged_points, tsys_dict)