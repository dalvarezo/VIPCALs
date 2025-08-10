import gc
import random
import warnings
import numpy as np

import functools
print = functools.partial(print, flush=True)

from collections import defaultdict

from scripts.helper import Antenna, Scan
from scripts.helper import ddhhmmss, tacop

import Wizardry.AIPSData as wizard

from AIPSTask import AIPSTask
AIPSTask.msgkill = -8 

def refant_choose_snr(data, sources, target_list, full_source_list, \
                      log_list, search_central = True, max_scans = 10):
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
    :param search_central: search for reference antenna only between \
                            KP, LA, PT, OV and FD, defaults to True
    :type search_central: bool, optional
    :max_scans: maximum number of scans per source where to compute the SNR; defaults 
        to 10
    :type max_scans: int
    :return: reference antenna number, sorted antenna dictionary containing the SNR
    :rtype: int, dict
    """     
    # Load tables
    nx_table = data.table('NX', 1)
    an_table = data.table('AN', 1)
    
    # Collect info from antennas participating in the observation
    antennas_dict = {}

    for ant in an_table:
        a = Antenna()
        a.name = ant['anname'].strip()
        a.id = ant['nosta']
        a.coords = np.array(ant['stabxyz'])
        a.set_codename()
        antennas_dict[a.id] = a

    # Remove antennas with no TY or GC information
    gc_antennas = [y['antenna_no'] for y in data.table('GC',1)]
    ty_antennas = [t['antenna_no'] for t in data.table('TY',2)]
    ty_antennas = list(set(ty_antennas))

    bad_antennas = [z for z in list(antennas_dict.keys()) if z \
                    not in ty_antennas or z not in gc_antennas]
    for element in bad_antennas:
        del antennas_dict[element]

    # Where is the physical center of the array?
    center_coord = np.array([0,0,0])
    for ant in antennas_dict:
        center_coord = center_coord + antennas_dict[ant].coords 
    center_coord = center_coord/len(antennas_dict)
    
    # Distance of each antenna to the center
    for ant in antennas_dict:
        vector_dist = antennas_dict[ant].coords - center_coord
        antennas_dict[ant].dist = vector_dist.dot(vector_dist)

    wuvdata = wizard.AIPSUVData(data.name, data.klass, data.disk, \
                                data.seq)  # Wizardry version of the data
    
    inttime =  float(round(min([x.inttim for x  in wuvdata]), 2))   # Minimum integration time, needed
                                                                # for KRING

    # Create scan list
    time_to_antennas = index_visibility_antennas(wuvdata, bad_antennas)
    flagged_antennas = get_flagged_antennas(data)
    scan_list = []
    for i, scans in enumerate(nx_table):
        s = Scan()
        s.id = i
        s.time = scans['time']
        s.time_interval = scans['time_interval']
        s.len = scans['time_interval']
        s.source_id = scans['source_id']
        s.get_antennas(time_to_antennas)
        if len(is_flagged_scan(s, flagged_antennas)) < 2:
            continue
        scan_list.append(s)

    # Free memory
    del wuvdata

    # Give scans a source_name
    for sc in scan_list:
        for so in data.table('SU', 1):
            if sc.source_id == so.id__no:
                sc.source_name = so.source.strip()

    # Drop scans with no antennas observing or 0 seconds of observing time
    for s in scan_list:
        if len(s.antennas) == 0:
            scan_list.remove(s)
    for s in scan_list:
        if s.time_interval == 0.0:
            scan_list.remove(s)
    # How many scans did each antenna observe
    for ant in antennas_dict:
        for scn in scan_list:
            if antennas_dict[ant].id in scn.antennas:
                antennas_dict[ant].scans_obs.append(scn.id)
        antennas_dict[ant].max_scans = len(scan_list)

    # Maximum number of scans observed
    max_scan_no = np.max([len(antennas_dict[x].scans_obs) for x in antennas_dict])

    # Print a warning if no antennas was available in all scans
    if max_scan_no < len(scan_list):
        for pipeline_log in log_list:
            pipeline_log.write('\nWARNING: No antenna was available for all scans\n')
        print('\nWARNING: No antenna was available for all scans\n')

    # If there are antennas available in all scans, drop the rest
    else:
        bad_antennas = [x for x in antennas_dict if len(antennas_dict[x].scans_obs) < len(scan_list)]
        if len(bad_antennas) > 0:
            print('The following antennas are not available in all scans and will '
                  + f'not be considered for the main reference antenna:\n {[antennas_dict[k].codename for k in bad_antennas]}\n')
            for pipeline_log in log_list:
                pipeline_log.write('The following antennas are not available in all scans and will '
                  + f'not be considered for the main reference antenna:\n {[antennas_dict[k].codename for k in bad_antennas]}\n')
        for element in list(set(bad_antennas)):
            del antennas_dict[element]
            
    # Drop antennas if not available on the targets scans
    target_ids = [x.id for x in full_source_list if x.name in target_list]
    target_scans = [x for x in scan_list if x.source_id in target_ids]
    bad_antennas = []
    for ant in antennas_dict:
        for scan in target_scans:
            if scan.id not in antennas_dict[ant].scans_obs:
                bad_antennas.append(ant)
        
    if set(antennas_dict.keys()).intersection(set(bad_antennas)) == set(antennas_dict.keys()):
        for pipeline_log in log_list:
            pipeline_log.write('\nWARNING: No antenna was available for all target scans\n')
        print('\nWARNING: No antenna was available for all target scans\n')
    else:
        if len(bad_antennas) > 0:
            print('The following antennas are not available for all the science target(s) scans and will '
                  + f'not be considered for the main reference antenna:\n{[antennas_dict[k].codename for k in bad_antennas]}\n')
            for pipeline_log in log_list:
                pipeline_log.write('The following antennas are not available for all the science target(s) scans and will '
                  + f'not be considered for the main reference antenna:\n{[antennas_dict[k].codename for k in bad_antennas]}\n')
        for element in list(set(bad_antennas)):
            del antennas_dict[element]

    # Define the dictionary with the antennas
    snr_dict = {}
    for i in antennas_dict:
        if search_central == True:  # Search for refant only in the central antennas
            if antennas_dict[i].name in ['KP', 'LA', 'PT', 'OV', 'FD']:
                snr_dict[i] = {}
                for j in range(len(an_table)):
                    snr_dict[i][j+1] = []

        if search_central == False:  # Search for refant in all antennas
            snr_dict[i] = {}
            for j in range(len(an_table)):
                snr_dict[i][j+1] = []

    # If search_central == True, but none of the 5 central antennas was available, do it 
    # again with all antennas
    if search_central == True and len(snr_dict) == 0:
        for i in antennas_dict:
            snr_dict[i] = {}
            for j in range(len(an_table)):
                snr_dict[i][j+1] = []

    # If not, print the antennas that have been lost
    if search_central == True and len(snr_dict) > 0:
        non_central_ants = [antennas_dict[n].codename for n in antennas_dict if antennas_dict[n].name not in ['KP', 'LA', 'PT', 'OV', 'FD']]
        if len(non_central_ants) == 1:
            print(f'The following antenna is not a central antenna and will not be considered for the main reference antenna.\n{non_central_ants}\n')
            for pipeline_log in log_list:
                pipeline_log.write(f'The following antenna is not a central antenna and will not be considered for the main reference antenna:\n{non_central_ants}\n')

        if len(non_central_ants) > 1:
            print(f'The following antennas are not a central antenna and will not be considered for the main reference antenna.\n{non_central_ants}\n')
            for pipeline_log in log_list:
                pipeline_log.write(f'The following antennas are not a central antenna and will not be considered for the main reference antenna:\n{non_central_ants}\n')
        for element in [n for n in antennas_dict if antennas_dict[n].name not in ['KP', 'LA', 'PT', 'OV', 'FD']]:
            del antennas_dict[element]

    # Randomly select a maximum of max_scans of each source
    random.seed(42)
    rndm_scans = scan_list.copy()
    random.shuffle(rndm_scans)

    count = defaultdict(int)
    selected_scans = []

    for scn in rndm_scans:
        if count[scn.source_name] < max_scans:
            selected_scans.append(scn)
            count[scn.source_name] += 1

    # Run a fringe fit with each of the remaining antennas for the selected scans      
    for ant in antennas_dict:
        if ant in snr_dict.keys():
            refant_fring(data, ant, selected_scans)
            #refant_kring(data, ant, selected_scans, inttime)
            # Check the last SN table and store the median SNR (computed over IFs)
            last_table = data.table('SN', 0)
            for entry in last_table:
                snr_dict[ant][entry['antenna_no']].append(np.nanmedian(entry['weight_1']))
            # Remove table
            data.zap_table('SN', 0)

    # Get the mean value over sources
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=RuntimeWarning, message='Mean of empty slice.')
        warnings.filterwarnings('ignore', category=RuntimeWarning, message='Mean of empty slice')
        for i in antennas_dict:
            if i in snr_dict.keys():
                for j in range(len(an_table)):
                    snr_dict[i][j+1] = np.nanmean(snr_dict[i][j+1])

    # Order by median SNR (computed over baselines)
    median_snr_dict = {}
    for ant in antennas_dict:
        if ant in snr_dict.keys():
            median_snr_dict[ant] =  np.nanmedian(list(snr_dict[ant].values()))
            antennas_dict[ant].median_SNR = np.nanmedian(list(snr_dict[ant].values()))
    final_list = sorted(median_snr_dict, key = median_snr_dict.get, reverse = True)

    refant = final_list[0]

    return(refant, dict(sorted(antennas_dict.items(), key=lambda x: x[1].median_SNR, reverse=True)))


def refant_fring(data, refant, selected_scans, delay_w = 1000, \
                       rate_w = 200):
    """Short fringe fit (only FFT) to select a reference antenna.
    
    Fringe fit each IF, solving for delays and rates. Default values for 
    the delay and rate windows are 1000 ns and 200hz. Runs the FRING task in AIPS for 
    each of the selected scans and then merges them into a single SN table. 

    Creates a new SN table which contains the SNR per scan. 

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param selected_scans: list of scans where to compute the SNR
    :type selected_scans: list of :class:`~vipcals.scripts.helper.Scan` objects
    :param delay_w: delay window in ns in which the search is performed, defaults to 1000
    :type delay_w: int, optional
    :param rate_w: rate window in hz in which the search is performed, defaults to 200
    :type rate_w: int, optional  
    """    
    # Get the current highest SN table
    current_SN = data.table_highver('SN')
    
    for n, scan in enumerate(selected_scans):
        gc.collect()

        init_time = ddhhmmss(scan.time - scan.time_interval/1.95)
        final_time = ddhhmmss(scan.time + scan.time_interval/1.95)
        timeran = [None] + init_time.tolist() + final_time.tolist()

        # Solution interval is set as the scan length
        solint = scan.time_interval*24*60


        refant_fring = AIPSTask('fring')
        refant_fring.inname = data.name
        refant_fring.inclass = data.klass
        refant_fring.indisk = data.disk
        refant_fring.inseq = data.seq
        refant_fring.refant = refant
        refant_fring.docalib = 1    # Apply CL tables
        refant_fring.gainuse = 0    # Apply the latest CL table
        refant_fring.solint = solint

        refant_fring.timeran = timeran
        
        refant_fring.aparm[1] = 2    # At least 2 antennas per solution
        refant_fring.aparm[5] = 0    # Solve each IFs separately
        refant_fring.aparm[6] = 2    # Amount of information printed
        refant_fring.aparm[7] = 1    # SNR cutoff   
        
        refant_fring.dparm[1] = 1        # Number of baseline combinations searched
        refant_fring.dparm[2] = delay_w   # Delay window (ns) 0 => Full Nyquist range
        refant_fring.dparm[3] = rate_w    # Rate window (mHz) 0 => Full Nyquist range
        refant_fring.dparm[5] = 1        # Stop at the FFT step
        
        refant_fring.snver = 0       # One more than the highest existing version
        
        #print(vars(refant_fring))
        #exit()
        refant_fring.flagver = -1

        refant_fring.go()

    # Merge the tables in one

    if n > 0:
        clcal_merge = AIPSTask('clcal')
        clcal_merge.inname = data.name
        clcal_merge.inclass = data.klass
        clcal_merge.indisk = data.disk
        clcal_merge.inseq = data.seq

        clcal_merge.opcode = 'MERG'
        clcal_merge.snver = current_SN + 1 # First table to merge
        clcal_merge.invers = current_SN + n + 1 # Last table to merge
        clcal_merge.refant = refant

        clcal_merge.go()

    # remove previous tables and leave only the merged one
    if n > 0:
        for i in range (current_SN+1, current_SN+n+2):
            data.zap_table('SN', i)
        tacop(data, 'SN', current_SN+n+2, current_SN+1)
        data.zap_table('SN', current_SN+n+2) 


def get_flagged_antennas(data):
    """Return a set of antennas flagged due to 'NO TSYS/GC'."""
    if [1, 'AIPS FG'] not in data.tables:
        return set()
    fg_table = data.table('FG', 0)
    return {
        row['ants'][0] for row in fg_table
        if row['reason'].strip() == 'NO TSYS/GC'
    }

def is_flagged_scan(scan, flagged_antennas):
    """Filter out flagged antennas from the scan."""
    return [a for a in scan.antennas if a not in flagged_antennas]


def index_visibility_antennas(wuvdata, bad_antennas):
    """Build a time-indexed mapping of antennas participating in visibilities.

    Iterates over all visibilities in the given AIPSUVData object and records the
    antennas involved at each timestamp, excluding autocorrelations and any antennas
    marked as bad. This mapping can be used to quickly determine which antennas
    were observing during specific time intervals, avoiding repeated iteration over
    the full visibility dataset.

    :param wuvdata: Wizardry AIPSUVData object
    :type wuvdata: wizard.AIPSUVData
    :param bad_antennas: List of antenna IDs to exclude
    :type bad_antennas: list of int
    :return: Dictionary mapping visibility timestamps to sets of active antenna IDs
    :rtype: dict[float, set[int]]
    """    
    time_to_antennas = defaultdict(set)
    bad_set = set(bad_antennas)

    for vis in wuvdata:
        ant1, ant2 = vis.baseline
        if ant1 == ant2 or ant1 in bad_set or ant2 in bad_set:
            continue
        time_to_antennas[vis.time].update((ant1, ant2))

    return time_to_antennas


def refant_kring(data, refant, selected_scans, inttime, delay_w = 1000, \
                       rate_w = 200):
    """TEST

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param selected_scans: list of scans where to compute the SNR
    :type selected_scans: list of :class:`~vipcals.scripts.helper.Scan` objects
    :param delay_w: delay window in ns in which the search is performed, defaults to 1000
    :type delay_w: int, optional
    :param rate_w: rate window in hz in which the search is performed, defaults to 200
    :type rate_w: int, optional  
    """    
    # Get the current highest SN table
    current_SN = data.table_highver('SN')
    
    for n, scan in enumerate(selected_scans):

        # Set as solint the scan length
        solint = scan.time_interval*24*60

        if solint > 10:
            solint = 9.9

        init_time = ddhhmmss(scan.time - scan.time_interval/1.95)
        final_time = ddhhmmss(scan.time + scan.time_interval/1.95)
        timeran = [None] + init_time.tolist() + final_time.tolist()


        refant_kring = AIPSTask('kring')
        refant_kring.inname = data.name
        refant_kring.inclass = data.klass
        refant_kring.indisk = data.disk
        refant_kring.inseq = data.seq

        refant_kring.timeran = timeran

        refant_kring.refant = refant
        refant_kring.search = [None, refant]

        refant_kring.docalib = 1    # Apply CL tables
        refant_kring.gainuse = 0    # Apply the latest CL table

        refant_kring.solint = solint

        refant_kring.soltype = 'NOLS' # Stop at the FFT step
        refant_kring.solmode = 'NRD'

        refant_kring.cparm[1] = inttime           # Minimum integration time of the data
        refant_kring.cparm[2] = delay_w     # Delay window (ns) 0 => Full Nyquist range
        refant_kring.cparm[3] = rate_w      # Rate window (mHz) 0 => Full Nyquist range
        refant_kring.cparm[4] = 5           # SNR cutoff
        refant_kring.cparm[5] = 1           # Number of baseline combinations searched
        refant_kring.cparm[6] = 1           # Use only the antennas in search as refants
        
        refant_kring.snver = 0      # One more than the highest existing version
        
        refant_kring.prtlev = 2     # Amount of information printed

        print(vars(refant_kring))

        refant_kring.go()

    # Merge the tables in one

    if n > 0:
        clcal_merge = AIPSTask('clcal')
        clcal_merge.inname = data.name
        clcal_merge.inclass = data.klass
        clcal_merge.indisk = data.disk
        clcal_merge.inseq = data.seq

        clcal_merge.opcode = 'MERG'
        clcal_merge.snver = current_SN + 1 # First table to merge
        clcal_merge.invers = current_SN + n + 1 # Last table to merge
        clcal_merge.refant = refant

        clcal_merge.go()

    # remove previous tables and leave only the merged one
    if n > 0:
        for i in range (current_SN+1, current_SN+n+2):
            data.zap_table('SN', i)
        tacop(data, 'SN', current_SN+n+2, current_SN+1)
        data.zap_table('SN', current_SN+n+2) 