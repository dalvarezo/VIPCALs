import numpy as np
import Wizardry.AIPSData as wizard


class AntennaTY():
    """Obvserving Antennas."""
    def __init__(self):
        self.name = None
        self.id = None
        self.sources_obs = []
        self.tsys = []
        self.ty_times = []
        self.flag_value = None
        self.disp = 999
        self.mean_n_points = 0
        self.coords = None
        self.dist = None
        self.times_obs = None


class Scan():
    """Scans within an observation."""        
    def __init__(self):
        self.number = None
        self.itime = None
        self.ftime = None
        self.len = None
        self.source_id = None
        self.source_name = None
        self.antennas = []
    def get_antennas(self, wuvdata):
        for vis in wuvdata:
            if (vis.time < self.ftime) and (vis.time > self.itime):
                self.antennas.append(vis.baseline[0])
                self.antennas.append(vis.baseline[1])
        self.antennas = list(set(self.antennas))
    
    
    
def refant_choose(data, sources, full_source_list, pipeline_log):
    """Choose a suitable reference antenna

    It chooses a reference antenna based on its availability, stability of system \
    temperatures, and proximity to the center of the array.

    :param data: visibility data
    :type data: AIPSUVData
    :param sources: list with source names
    :type sources: list of str
    :param full_source_list: list containing all sources in the dataset
    :type full_source_list: list of Source objects
    :param pipeline_log: pipeline log
    :type pipeline_log: file
    :return: reference antenna number
    :rtype: int
    """    
    # Load tables
    nx_table = data.table('NX', 1)
    ty_table = data.table('TY', 2)
    an_table = data.table('AN', 1)
    
    # Which sources are relevant?
    sources_codes = []
    for src in full_source_list:
        if src.name in sources:
            sources_codes.append(src.id)

    # Collect info from antennas participating in the observation
    antennas_list = {}

    for ant in an_table:
        a = AntennaTY()
        a.name = ant['anname'].strip()
        a.id = ant['nosta']
        a.coords = np.array(ant['stabxyz'])
        antennas_list[a.id] = a

    # Where is the physical center of the array?
    center_coord = np.array([0,0,0])
    for ant in antennas_list:
        center_coord = center_coord + antennas_list[ant].coords 
    center_coord = center_coord/len(antennas_list)
    
    # Distance of each antenna to the center
    for ant in antennas_list:
        vector_dist = antennas_list[ant].coords - center_coord
        antennas_list[ant].dist = vector_dist.dot(vector_dist)


    wuvdata = wizard.AIPSUVData(data.name, data.klass, data.disk, \
                                data.seq)  # Wizardry version of the data

    # Create scan list
    scan_list = []
    for i, scans in enumerate(nx_table):
        s = Scan()
        s.number = i
        s.itime = scans['time'] - scans['time_interval']/2
        s.ftime = scans['time'] + scans['time_interval']/2
        s.len = scans['time_interval']
        s.source_id = scans['source_id']
        s.get_antennas(wuvdata)
        scan_list.append(s)
        
    # Add tsys values to the antennas
    for point in ty_table:
        # Exclude non loaded sources
        if point['source_id'] not in sources_codes:
            continue
        try:
            antennas_list[point['antenna_no']].flag_value = point['tant_1'][0]
        except TypeError: # Single IF datasets
            antennas_list[point['antenna_no']].flag_value = point['tant_1']
            
        antennas_list[point['antenna_no']].sources_obs.\
            append(point['source_id'])
        antennas_list[point['antenna_no']].ty_times.append(point['time'])  
        # Replace flagged values with NaN
        try:
            for ind,ty in enumerate(point['tsys_1']):
                if ty == antennas_list[point['antenna_no']].flag_value:
                    point['tsys_1'][ind] = np.NaN
        except TypeError: # Single IF datasets
            if point['tsys_1'] == antennas_list[point['antenna_no']].flag_value:
                point['tsys_1'] = np.NaN
                
        # Append system temperature
        antennas_list[point['antenna_no']].tsys.append(point['tsys_1'])

    # Drop antennas not available through the entire observation
    # There is a bug, in which the problem is in the source, not in the antenna, this discards
    # all antennas although they are fine (for example in VLBA_BB240GM_bb240gm_BIN0_SRC0_0_120103T152643.idifits)
    # with J0530+1331. This step needs to be thought of again.
    bad_antennas = []
    for ant in antennas_list:
        for scn in scan_list:
            if antennas_list[ant].id not in scn.antennas:
                bad_antennas.append(ant)
                
    pipeline_log.write('\n')
    for element in list(set(bad_antennas)):
        
        pipeline_log.write(antennas_list[element].name + ' has been '\
                           + 'discarded in the search. It is not available ' \
                           + 'in ' + str(bad_antennas.count(element))\
                           + ' scans out of ' + str(len(scan_list)) + '.\n')
            
        print(antennas_list[element].name + ' has been discarded in '\
              + 'the search. It is not available in ' \
              + str(bad_antennas.count(element)) + ' scans out of ' \
              + str(len(scan_list)) + '.\n')
        del antennas_list[element]


    # Group temperatures by antenna and source
    temp_dict = {}
    for ant in antennas_list:
        temp_dict[antennas_list[ant].name] = {}
        for source in list(set(antennas_list[ant].sources_obs)):
            temp_dict[antennas_list[ant].name][source] = []
        for i, tsys in enumerate(antennas_list[ant].tsys):
            temp_dict[antennas_list[ant].name][antennas_list[ant].\
                                               sources_obs[i]].append(tsys)
                
    # REDUNDANT STEP, SHOULD BE DELETED
    # # Drop antennas that didn't measure temperature in all sources

    # bad_antennas = []
    # for ant in temp_dict:
    #     if temp_dict[ant].keys() != set(sources_codes):
    #         bad_antennas.append(ant)       
            
    # for name in bad_antennas:
    #     del temp_dict[name]
    #     for ant in antennas_list:
    #         if name == antennas_list[ant].name:
    #             del antennas_list[ant]
    #             break
                    
    # If at this point there are more than 3 antennas, take the 3 that are 
    # closest to the center of the array
    
    if len(temp_dict) > 3:
        bad_antennas = []
        bad_keys= sorted(antennas_list, \
                            key = lambda x: antennas_list[x].dist)[3:] 
        for num in bad_keys:
            bad_antennas.append(antennas_list[num].name)
        for name in bad_antennas:
            del temp_dict[name]
        
    # Transform the lists into np arrays and compute the std per IF
    std_dict = {}
    for ant in temp_dict:
        std_dict[ant] = {}
        for source in temp_dict[ant]:
            temp_dict[ant][source] = np.asarray(temp_dict[ant][source])
            std_dict[ant][source] = np.nanstd(temp_dict[ant][source], axis = 0)

    # Median between IFs and between sources
    median_if_dict = {}
    for ant in std_dict:
        median_if_dict[ant] = []
        for source in std_dict[ant]:
            median_if_dict[ant].append(np.median(std_dict[ant][source]))
        median_if_dict[ant] = np.median(median_if_dict[ant])


    # Order by dispersion 
    final_list = sorted(median_if_dict.items(), reverse = False)
    
    # If there is no antenna available, choose FD and issue a warning
    if len(final_list) == 0:
        # Reload the antenna list
        for ant in an_table:
            a = AntennaTY()
            a.name = ant['anname'].strip()
            a.id = ant['nosta']
            a.coords = np.array(ant['stabxyz'])
            antennas_list[a.id] = a
            
        for ant in antennas_list:
            if antennas_list[ant].name == 'FD':
                refant = antennas_list[ant].id
                pipeline_log.write('WARNING: No antenna was available through'\
                                   + ' the entire observation. The chosen '\
                                   + 'reference antenna is FD. Be aware that '\
                                   + 'some data could be lost and that a '\
                                   + 'better choice could be made.\n')
                                       
                print('WARNING: No antenna was available through the entire '\
                      + 'observation. The chosen reference antenna is FD. Be '\
                      + 'aware that some data could be lost and that a better'\
                      + ' choice could be made.\n')
            else:
                refant = 404
                
        # If FD is not available, use LA
        if refant == 404:
            for ant in antennas_list:
                if antennas_list[ant].name == 'LA':
                    refant = antennas_list[ant].id
                    pipeline_log.write('WARNING: No antenna was available '\
                                       + 'through the entire observation. The'\
                                       + ' chosen reference antenna is LA. Be'\
                                       + ' aware that some data could be lost'\
                                       + ' and that a better choice could be '\
                                       + 'made.\n')
                                           
                    print('WARNING: No antenna was available through the ' \
                          + 'entire observation. The chosen reference ' \
                          + 'antenna is LA. Be aware that some data could be '\
                          + 'lost and that a better choice could be made.\n')
                    break 
                else:
                    refant = 404
                
        # If none of them is available, use KP
        if refant == 404:
            for ant in antennas_list:
                if antennas_list[ant].name == 'KP':
                    refant = antennas_list[ant].id
                    pipeline_log.write('WARNING: No antenna was available '\
                                       + 'through the entire observation. The'\
                                       + ' chosen reference antenna is KP. Be'\
                                       + ' aware that some data could be lost'\
                                       + ' and that a better choice could be '\
                                       + 'made.\n')
                                           
                    print('WARNING: No antenna was available through the ' \
                          + 'entire observation. The chosen reference ' \
                          + 'antenna is KP. Be aware that some data could be '\
                          + 'lost and that a better choice could be made.\n')
                    break
                else:
                    refant = 404
        # If none of the three is available I should print an error in the 
        # main workflow
        return(refant)

    # Median Tsys
    median_tsys = 99999
    for ant in antennas_list:
        if antennas_list[ant].name == final_list[0][0]:
            median_tsys = np.nanmedian(antennas_list[ant].tsys)
            refant = antennas_list[ant].id
    
    pipeline_log.write('The chosen reference antenna is ' + final_list[0][0]\
                       + '. It is available for all scans, its median '\
                       + 'temperature is {:.2f} K'.format(median_tsys) \
                       + ', with a median dispersion of '\
                       + '{:.2f} K.\n'.format(final_list[0][1]))
    print('The chosen reference antenna is ' + final_list[0][0] + '. It is '\
          + 'available for all scans, its median temperature is  '\
          + '{:.2f} K'.format(median_tsys) + ', with a median dispersion of '\
          + '{:.2f} K.\n'.format(final_list[0][1]))


    return(refant)