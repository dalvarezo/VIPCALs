from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

import numpy as np
import os

from random import sample 


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

def snr_fring_optimiz(data, refant, solint, timeran, source, output_version,\
                      delay_w = 1000, rate_w = 200):
    """Short fringe fit (only FFT) to obtain an SNR value.
    
    Fringe fit of all IF's together, solving for delays and rates.
    The solution interval, the timerange, the source and theoutput SN version
    need to be specified. 

    Creates a SN table containing the SNR values
    
    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param solint: solution interval in minutes, if 0 => solint = 10 min, \
                   if > scan  => solint = scan; defaults to 0
    :type solint: int, optional
    :param timeran: time range in which the search is performed
    :type timeran: AIPSList
    :param source: name of the source on which to perform the fringe fit
    :type source: str
    :param output_version: output version of the SN table
    :type output_version: int
    :param delay_w: delay window in ns in which the search is performed, defaults to 1000
    :type delay_w: int, optional
    :param rate_w: rate window in hz in which the search is performed, defaults to 200
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
    
    optimiz_fring.aparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    optimiz_fring.aparm[1] = 2    # At least 2 antennas per solution
    optimiz_fring.aparm[5] = 1    # Solve all IFs together
    optimiz_fring.aparm[6] = 2    # Amount of information printed
    optimiz_fring.aparm[7] = 1    # NO SNR cutoff   
    
    optimiz_fring.dparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    optimiz_fring.dparm[1] = 1    # Number of baseline combinations searched
    optimiz_fring.dparm[2] = delay_w   # Delay window (ns) 0 => Full Nyquist 
                                       # range
    optimiz_fring.dparm[3] = rate_w    # Rate window (mHz) 0 => Full Nyquist 
                                       # range
    optimiz_fring.dparm[5] = 1    # Stop at the FFT step
    #optimiz_fring.dparm[9] = 1    # Do NOT fit rates    
    
    optimiz_fring.msgkill = -4
    
    optimiz_fring.go()

def get_optimal_scans(target, optimal_scans, full_source_list):
    """Get the optimal scans for an specific target

    Get the scans where the target has been observed from the optimal scan list. Optimal \
    means that the maximum number of antennas was observing the source. 

    :param target: source name
    :type target: str
    :param optimal_scans: list of scans in which the maximum number of antennas were \
                          observing
    :type optimal_scans: list of Scan objects
    :param full_source_list: list containing all sources in the dataset
    :type full_source_list: list of Source objects
    :return: optimal scans for the target
    :rtype: list of Scan objects
    """    
    target_id = next(source for source in full_source_list \
                     if source.name == target).id
        
    target_optimal_scans = list(filter(lambda x: x.id == target_id,\
                                       optimal_scans))
        
    if len(target_optimal_scans) > 5:
        target_optimal_scans = sample(target_optimal_scans, 5)
        
    return(target_optimal_scans)
        
def optimize_solint(data, target, target_optimal_scans, refant):
    """Find the optimal solution interval in which to fringe fit a target.

    Runs a fringe fit in a selected number of scans of the target for five different \
    solution intervals: 1/5, 1/4, 1/3, 1/2, and 1/1 of the scan length. The optimal \
    solution interval is the smallest time required for all baselines to reach and SNR \
    of 6. If this condition is not met, then the solution interval is the scan length.

    :param data: visibility data
    :type data: AIPSUVData
    :param target: source name
    :type target: str
    :param target_optimal_scans: optimal scans for the target
    :type target_optimal_scans: list of Scans objects
    :param refant: reference antenna number
    :type refant: int
    :return: optimal solution interval in minutes
    :rtype: float
    """    
    # If there were no optimal scans for the target, then return 10 as
    # the solint. Not optimal, we should rethink it
    if len(target_optimal_scans) == 0:
        return(10)
    # Get scan length (assuming them equal) in minutes
    scan_length = target_optimal_scans[0].time_interval*24*60
    for solint in np.round([scan_length/5.1, scan_length/4.1, \
                            scan_length/3.1, scan_length/2.1, scan_length],1):
        snr_dict = {}
        # Initialize dictionary
        for a in target_optimal_scans[0].antennas:
            snr_dict[a] = []
        for i, scan in enumerate(target_optimal_scans):
            # Get the timerange of the scan
            scan_time = scan.time
            scan_time_interval = scan.time_interval
            init_time = ddhhmmss(scan_time - scan_time_interval/1.8)
            final_time = ddhhmmss(scan_time + scan_time_interval/1.8)
            timerang = [None] + init_time.tolist() + final_time.tolist()
            # print(timerang)
            # Perform an SNR fringe fit
            snr_fring_optimiz(data, refant, float(solint), timerang, \
                              AIPSList(target), 6)
                
            snr_table = data.table('SN', 6)
            # Save the SNR of the scan
            
            for antennas in snr_table:
                if antennas['antenna_no'] == refant:
                    snr_dict[antennas['antenna_no']].append(6.5)
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
        for key in snr_dict.keys():
            snr_values.append(np.median(snr_dict[key]))
	#Check if they are all over 5.5
        if all([x > 5.5 for x in snr_values]) == True:
            break
    return(solint)

    # I should modify this function in such a way that can produce plots with
    # the SNR as a function of the solution interval for each baseline