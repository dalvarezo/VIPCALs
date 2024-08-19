import numpy as np
import Wizardry.AIPSData as wizard

from AIPSTask import AIPSTask, AIPSList


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
        self.scans_obs = []


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
    
    
    

def refant_choose_snr(data, sources, target_list, full_source_list, log_list):
    """Choose a suitable reference antenna using SNR values

    Select antennas based on its availability throughout the observation, then run a \
    fast fringe fit on the target(s) using each antenna as the reference antenna. Return \
    the id of the antenna with the highest SNR.

    :param data: visibility data
    :type data: AIPSUVData
    :param sources: list with source names
    :type sources: list of str
    :param target_list: target names
    :type target_list: list of str
    :param full_source_list: list containing all sources in the dataset
    :type full_source_list: list of Source objects
    :param log: list of pipeline logs
    :type log_list: list of file
    :return: reference antenna number
    :rtype: int
    """     
    # Load tables
    nx_table = data.table('NX', 1)
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

    # How many scans did each antenna observe
    for ant in antennas_list:
        for scn in scan_list:
            if antennas_list[ant].id in scn.antennas:
                antennas_list[ant].scans_obs.append(scn.number)
    # Maximum number of scans observed
    max_scan_no = np.max([len(antennas_list[x].scans_obs) for x in antennas_list])
    # Print a warning if no antennas was available in all scans
    if max_scan_no < len(scan_list):
        for pipeline_log in log_list:
            pipeline_log.write('\nWARNING: No antenna was available for all scans\n')
        print('\nWARNING: No antenna was available for all scans\n')

    # Drop antennas if not available on the targets scans, --- or not available in the max
    # number of scans --- omitted this second part for now
    target_ids = [x.id for x in full_source_list if x.name in target_list]
    target_scans = [x for x in scan_list if x.source_id in target_ids]
    bad_antennas = []
    for ant in antennas_list:
        #if len(antennas_list[ant].scans_obs) < len(scan_list):
        #    bad_antennas.append(ant)
        #    continue
        for scan in target_scans:
            if scan.number not in antennas_list[ant].scans_obs:
                bad_antennas.append(ant)
        
    for element in list(set(bad_antennas)):
        del antennas_list[element]

    # Run a fringe fit with the remaining antennas
    snr_dict = {}
    for i in antennas_list:
        snr_dict[i] = {}
        for j in range(len(an_table)):
            snr_dict[i][j+1] = []

    for ant in antennas_list:
        dummy_fring(data, ant, target_list)
        # Check the last SN table and store the median SNR (computed over IFs)
        last_table = data.table('SN', 0)
        for entry in last_table:
            snr_dict[ant][entry['antenna_no']].append(np.median(entry['weight_1']))
        # Remove table
        data.zap_table('SN', 0)

    # Get the mean value over sources
    for i in antennas_list:
        for j in range(len(an_table)):
            snr_dict[i][j+1] = np.mean(snr_dict[i][j+1])

    # Order by median SNR (computed over baselines)
    median_snr_dict = {}
    for ant in antennas_list:
        median_snr_dict[ant] =  np.median(list(snr_dict[ant].values()))
    final_list = sorted(median_snr_dict, key = median_snr_dict.get, reverse = True)
    refant = final_list[0]

    for pipeline_log in log_list:
        pipeline_log.write('\n')
        pipeline_log.write(antennas_list[refant].name + ' has been selected as the ' \
                          + 'reference antenna. It is available in ' + str(max_scan_no) \
                          + ' out of ' + str(len(scan_list)) + ' scans.\nMedian SNR ' \
                          + 'value for the target on each baseline are:\n')
        for ant in antennas_list:
            if refant != ant:
                if refant < ant:
                    pipeline_log.write(str(refant) + '-' + str(ant) + ': ' \
                                    + '{:.2f}\n'.format(snr_dict[refant][ant]))
                if refant > ant:
                    pipeline_log.write(str(ant) + '-' + str(refant) + ': ' \
                                    + '{:.2f}\n'.format(snr_dict[refant][ant]))
        pipeline_log.write('MEDIAN SNR: {:.2f}\n'.format(median_snr_dict[refant]))
                
    print(antennas_list[refant].name + ' has been selected as the reference ' \
                        + 'antenna. It is available in ' + str(max_scan_no) + ' out ' \
                        + 'of ' + str(len(scan_list)) + ' scans.\nMedian SNR value ' \
                        + 'for the target on each baseline are:\n')
    for ant in antennas_list:
        if refant != ant:
            if refant < ant:
                print(str(refant) + '-' + str(ant) + ': ' \
                                    + '{:.2f}\n'.format(snr_dict[refant][ant]))
            if refant > ant:
                print(str(ant) + '-' + str(refant) + ': ' \
                                    + '{:.2f}\n'.format(snr_dict[refant][ant]))
                
    print('MEDIAN SNR: {:.2f}\n'.format(median_snr_dict[refant]))

    return(refant)

def refant_choose_tsys(data, sources, full_source_list, log_list):
    """Choose a suitable reference antenna using system temperatures

    It chooses a reference antenna based on its availability, stability of system \
    temperatures, and proximity to the center of the array.

    :param data: visibility data
    :type data: AIPSUVData
    :param sources: list with source names
    :type sources: list of str
    :param full_source_list: list containing all sources in the dataset
    :type full_source_list: list of Source objects
    :param log: list of pipeline logs
    :type log_list: list of file
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

    for pipeline_log in log_list:            
        pipeline_log.write('\n')
    for element in list(set(bad_antennas)):
        for pipeline_log in log_list:
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
    # It should ignore if they are 0!
    median_if_dict = {}
    for ant in std_dict:
        median_if_dict[ant] = []
        for source in std_dict[ant]:
            median_if_dict[ant].append(np.median(std_dict[ant][source]))
        median_if_dict[ant] = np.median(median_if_dict[ant])


    # Order by dispersion 
    final_list = sorted(median_if_dict, key = median_if_dict.get, reverse = False)
    
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
                for pipeline_log in log_list:
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
                    for pipeline_log in log_list:
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
                    for pipeline_log in log_list:
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
        if antennas_list[ant].name == final_list[0]:
            median_tsys = np.nanmedian(antennas_list[ant].tsys)
            refant = antennas_list[ant].id
    
    for pipeline_log in log_list:
        pipeline_log.write('The chosen reference antenna is ' + final_list[0]\
                        + '. It is available for all scans, its median '\
                        + 'temperature is {:.2f} K'.format(median_tsys) \
                        + ', with a median dispersion of '\
                        + '{:.2f} K.\n'.format(median_if_dict[final_list[0]]))
    print('The chosen reference antenna is ' + final_list[0] + '. It is '\
          + 'available for all scans, its median temperature is  '\
          + '{:.2f} K'.format(median_tsys) + ', with a median dispersion of '\
          + '{:.2f} K.\n'.format(median_if_dict[final_list[0]]))


    return(refant)

def dummy_fring(data, refant, target_list, solint = 0, delay_w = 1000, \
                       rate_w = 200):
    """Short fringe fit (only FFT) to select a reference antenna.
    
    Fringe fit each IF, solving for delays and rates. Default values for \
    the delay and rate windows are 1000 ns and 200hz.
    

    Creates a new SN table which contains the SNR per scan. 

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param target_list: target names
    :type target_list: list of str
    :param solint: solution interval in minutes, if 0 => solint = 10 min, \
                   if > scan  => solint = scan; defaults to 0
    :type solint: int, optional
    :param delay_w: delay window in ns in which the search is performed, defaults to 1000
    :type delay_w: int, optional
    :param rate_w: rate window in hz in which the search is performed, defaults to 200
    :type rate_w: int, optional  
    """    
    dummy_fring = AIPSTask('fring')
    dummy_fring.inname = data.name
    dummy_fring.inclass = data.klass
    dummy_fring.indisk = data.disk
    dummy_fring.inseq = data.seq
    dummy_fring.refant = refant
    dummy_fring.docalib = 1    # Apply CL tables
    dummy_fring.gainuse = 0    # Apply the latest CL table
    dummy_fring.solint = solint
    dummy_fring.calsour = AIPSList(target_list)
    
    dummy_fring.aparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    dummy_fring.aparm[1] = 2    # At least 2 antennas per solution
    dummy_fring.aparm[5] = 0    # Solve IFs separatedly
    dummy_fring.aparm[6] = 2    # Amount of information printed
    dummy_fring.aparm[7] = 5    # SNR cutoff   
    
    dummy_fring.dparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    dummy_fring.dparm[1] = 1    # Number of baseline combinations searched
    dummy_fring.dparm[2] = delay_w   # Delay window (ns) 0 => Full Nyquist range
    dummy_fring.dparm[3] = rate_w    # Rate window (mHz) 0 => Full Nyquist range
    dummy_fring.dparm[5] = 1    # Stop at the FFT step
    
    dummy_fring.snver = 0       # One more than the highest existing version
    dummy_fring.msgkill = -4
    
    dummy_fring.go()