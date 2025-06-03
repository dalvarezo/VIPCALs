import random
import warnings

import numpy as np

from scripts.helper import ddhhmmss

from AIPSTask import AIPSTask, AIPSList

AIPSTask.msgkill = -8

def snr_fring_optimiz(data, refant, solint, timeran, source, output_version,\
                      delay_w = 1000, rate_w = 200):
    """Short fringe fit (only FFT) to obtain an SNR value.
    
    Fringe fit of each IF, solving for delays and rates.
    The solution interval, the timerange, the source and the output SN version
    need to be specified.

    Creates a SN table containing the SNR values.
    
    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param solint: solution interval in minutes, if 0 => solint = 10 min, \
                   if > scan/2  => solint = scan
    :type solint: int
    :param timeran: time range in AIPS format in which the search is performed
    :type timeran: AIPSList
    :param source: name of the source on which to perform the fringe fit
    :type source: str
    :param output_version: output version of the SN table
    :type output_version: int
    :param delay_w: delay window in ns in which the search is performed; defaults to 1000
    :type delay_w: int, optional
    :param rate_w: rate window in mHz in which the search is performed; defaults to 200
    :type rate_w: int, optional 
    """    
    optimiz_fring = AIPSTask('fring')
    optimiz_fring.inname = data.name
    optimiz_fring.inclass = data.klass
    optimiz_fring.indisk = data.disk
    optimiz_fring.inseq = data.seq
    optimiz_fring.refant = refant
    optimiz_fring.docalib = 1    # Apply CL tables
    optimiz_fring.gainuse = 0    # Apply the latest CL table
    optimiz_fring.doband = 1    # Apply bandpass correction
    
    optimiz_fring.solint = solint
    optimiz_fring.timeran = timeran
    optimiz_fring.calsour = AIPSList([source])
    optimiz_fring.snver = output_version
    
    optimiz_fring.aparm[1] = 2    # At least 2 antennas per solution
    optimiz_fring.aparm[5] = 0    # Solve IFs separately
    optimiz_fring.aparm[6] = 2    # Amount of information printed
    optimiz_fring.aparm[7] = 1    # NO SNR cutoff  
    optimiz_fring.aparm[9] = 1    # Exhaustive search 
    
    optimiz_fring.dparm[1] = 1    # Number of baseline combinations searched
    optimiz_fring.dparm[2] = delay_w   # Delay window (ns) 0 => Full Nyquist 
                                       # range
    optimiz_fring.dparm[3] = rate_w    # Rate window (mHz) 0 => Full Nyquist 
                                       # range
    optimiz_fring.dparm[5] = 1    # Stop at the FFT step 

    optimiz_fring.go()

def optimize_solint_mm(data, target, target_scans, refant, min_solint = 1.0, 
                       max_solint = 10.0):
    """Find the optimal solution interval in which to fringe fit a target.

    Algorithm for mm-wavelengths

    Runs a fringe fit in a selected number of scans of the target for five different \
    solution intervals: 1/5, 1/4, 1/3, 1/2, and 1/1 of the scan length. The optimal \
    solution interval is the smallest time required for all baselines to reach an SNR \
    of 5. It will only search for solution intervals that are larger than min_solint.
    If there are more than 10 scans, the search will be done in 10 randomly selected 
    scans. 

    :param data: visibility data
    :type data: AIPSUVData
    :param target: source name
    :type target: str
    :param target_scans: list of scans where to optimize the solution interval
    :type target_scans: list of :class:`~vipcals.scripts.helper.Scan` objects
    :param refant: reference antenna number
    :type refant: int
    :param min_solint: minimum solution interval in minutes; defaults to 1
    :type min_solint: float, optional
    :param max_solint: minimum solution interval in minutes; defaults to 10
    :type max_solint: float, optional
    :return: optimal solution interval in minutes, dictionary with the SNR per antenna 
        for each solution interval
    :rtype: float, dict
    """    
    # If there are more than 10 scans, randomly select 10
    if len(target_scans) > 10:
        random.seed(42)
        target_scans = random.sample(target_scans, 10)

    # Get longest scan length in minutes
    solint_dict = {}
    scan_length = max(target_scans, key=lambda x: x.time_interval).time_interval*24*60
    for solint in np.round([scan_length/5.1, scan_length/4.1, \
                            scan_length/3.1, scan_length/2.1, scan_length],1):
        snr_dict = {}
        solint_dict[solint] = {}
        # Skip if below the minimum solution interval
        if solint < min_solint:
            solint_dict[solint] = "TOO SHORT"
            solint = min_solint
            continue
        # Skip if over the maximum solution interval
        if solint > max_solint:
            solint_dict[solint] = "TOO LONG"
            solint = max_solint
            continue
        # Get all antennas:
        all_ant = []
        for s in target_scans:
            all_ant += s.antennas
        all_ant = list(set(all_ant))
        # Initialize dictionary
        for a in all_ant:
            snr_dict[a] = []
        for i, scan in enumerate(target_scans):
            # If there are any antennas not initialized in the dictionary, then do so
            # This  might happen when different scans have different available antennas

            # Skip scans of length 0. Not sure how they arise though.
            if scan.time_interval == 0:
                continue
            for a in target_scans[i].antennas:
                if a not in snr_dict.keys():
                    snr_dict[a] = []
            # Get the timerange of the scan
            scan_time = scan.time
            scan_time_interval = scan.time_interval
            init_time = ddhhmmss(scan_time - scan_time_interval/1.8)
            final_time = ddhhmmss(scan_time + scan_time_interval/1.8)
            timerang = [None] + init_time.tolist() + final_time.tolist()

            # Perform an SNR fringe fit
            snr_fring_optimiz(data, refant, float(solint), timerang, \
                              AIPSList(target), 6)
                
            snr_table = data.table('SN', 6)
            # Save the SNR of the scan
            
            for antennas in snr_table:
                if antennas['antenna_no'] == refant:
                    snr_dict[antennas['antenna_no']].append(np.nan)
                else:
                    if type(antennas['weight_1']) == list:
                        snr_dict[antennas['antenna_no']] += [x/2  for x in antennas['weight_1']]
                    else:    # Single IF datasets
                        snr_dict[antennas['antenna_no']].append(antennas['weight_1']/2)

            # Delete the solution table
            data.zap_table('SN', 6)



        # Check if the median SNR across scans reaches the threshold
        snr_values = []
        # Compute the median per antenna
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning, message='All-NaN slice encountered')
            for key in snr_dict.keys():
                snr_values.append(np.nanmedian(snr_dict[key]))
                solint_dict[solint][key] = np.nanmedian(snr_dict[key])

	    #Check if they are all over 5, if so, get that solution interval
        if all([x > 5 for x in snr_values if np.isnan(x) == False]) == True:
            break

    return(solint, solint_dict)

def optimize_solint_cm(data, target, target_scans, refant, min_solint = 1.0):
    """Alternative algorithm to find the optimal solution interval for fringe fit.

    Runs a fringe fit in a selected number of scans of the target for five different 
    solution intervals: 1/5, 1/4, 1/3, 1/2, and 1/1 of the scan length. The optimal 
    solution interval is the one that produces the best SNR. It will only search for 
    solution intervals that are larger than min_solint. If there are more than 10 scans, 
    the search will be done in 10 randomly selected scans. 

    THIS ALGORITHM IS NOT USED IN THE CURRENT VERSION
    
    :param data: visibility data
    :type data: AIPSUVData
    :param target: source name
    :type target: str
    :param target_scans: list of scans where to optimize the solution interval
    :type target_scans: list of :class:`~vipcals.scripts.helper.Scan` objects
    :param refant: reference antenna number
    :type refant: int
    :param min_solint: minimum solution interval in minutes; defaults to 1
    :type min_solint: float, optional
    :return: optimal solution interval in minutes, dictionary with the median SNR for 
        each solution interval
    :rtype: float, dict
    """

    # If there are more than 10 scans, randomly select 10
    if len(target_scans) > 10:
        random.seed(42)
        target_scans = random.sample(target_scans, 10)

    # Get longest scan length in minutes
    solint_dict = {}
    scan_length = max(target_scans, key=lambda x: x.time_interval).time_interval*24*60
    for solint in np.round([scan_length/5.1, scan_length/4.1, \
                            scan_length/3.1, scan_length/2.1, scan_length],1):
        solint_dict[solint] = []
        snr_dict = {}
        # Initialize dictionary
        for a in target_scans[0].antennas:
            snr_dict[a] = []
        for i, scan in enumerate(target_scans):
            # If there are any antennas not initialized in the dictionary, then do so
            # This  might happen when different scans have different available antennas

            for a in target_scans[i].antennas:
                if a not in snr_dict.keys():
                    snr_dict[a] = []
            # Get the timerange of the scan
            scan_time = scan.time
            scan_time_interval = scan.time_interval
            init_time = ddhhmmss(scan_time - scan_time_interval/1.8)
            final_time = ddhhmmss(scan_time + scan_time_interval/1.8)
            timerang = [None] + init_time.tolist() + final_time.tolist()

            # Perform an SNR fringe fit
            snr_fring_optimiz(data, refant, int(solint), timerang, \
                              AIPSList(target), 6)
                
            snr_table = data.table('SN', 6)
            # Save the SNR of the scan
            
            for antennas in snr_table:
                if antennas['antenna_no'] == refant:
                    snr_dict[antennas['antenna_no']].append(np.nan)
                else:
                    try:
                        snr_dict[antennas['antenna_no']].append\
                        (antennas['weight_1'][0])
                    except TypeError:
                        snr_dict[antennas['antenna_no']].append\
                        (antennas['weight_1'])
                        
            # Delete the solution table
            data.zap_table('SN', 6)

        # Check if the median SNR across scans reaches the threshold
        snr_values = []
        # Compute the median per antenna
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning, message='All-NaN slice encountered')
            for key in snr_dict.keys():
                snr_values.append(np.nanmedian(snr_dict[key]))
            # Add median SNR of all antennas to dict
            solint_dict[solint] = np.nanmedian(snr_values)

    solint = list(dict(sorted(solint_dict.items(), key=lambda item: item[1], \
                              reverse = True)).keys())[0]
    
    return(solint, solint_dict)