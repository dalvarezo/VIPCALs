from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

import numpy as np
import os

class SNRScan():
    """Scans within an observation.""" ## SHOULD BE MERGED WITH THE Scan() CLASS
    def __init__(self):
        self.name = None
        self.id = None
        self.snr = []
        self.time = None
        self.time_interval = None
        self.antennas = []

def snr_fring(data, refant, solint = 0):
    """Short fringe fit to select a bright calibrator.
    
    Fringe fit of all IF's together, solving only for phases.

    Creates SN#3, which contains the SNR per scan.  

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param solint: solution interval in minutes, if 0 => solint = 10 min, \
                   if > scan  => solint = scan; defaults to 0
    :type solint: int, optional
    """    
    snr_fring = AIPSTask('fring')
    snr_fring.inname = data.name
    snr_fring.inclass = data.klass
    snr_fring.indisk = data.disk
    snr_fring.inseq = data.seq
    snr_fring.refant = refant
    snr_fring.docalib = 1    # Apply CL tables
    snr_fring.gainuse = 0    # Apply the latest CL table
    snr_fring.solint = solint
    
    snr_fring.aparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    snr_fring.aparm[1] = 2    # At least 2 antennas per solution
    snr_fring.aparm[5] = 1    # Solve all IFs together
    snr_fring.aparm[6] = 2    # Amount of information printed
    snr_fring.aparm[7] = 5    # SNR cutoff   
    
    snr_fring.dparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    snr_fring.dparm[1] = 1    # Number of baseline combinations searched
    snr_fring.dparm[2] = 500    # Delay window (ns)
    snr_fring.dparm[9] = 1    # Do NOT fit rates    
    
    snr_fring.snver = 3
    snr_fring.msgkill = -4
    
    snr_fring.go()
    
def snr_fring_only_fft(data, refant, solint = 0, delay_w = 1000, \
                       rate_w = 200):
    """Short fringe fit (only FFT) to select a bright calibrator.
    
    Fringe fit of all IF's together, solving for delays and rates. Default values for \
    the delay and rate windows are 1000 ns and 200hz.
    

    Creates SN#3, which contains the SNR per scan. 

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param solint: solution interval in minutes, if 0 => solint = 10 min, \
                   if > scan  => solint = scan; defaults to 0
    :type solint: int, optional
    :param delay_w: delay window in ns in which the search is performed, defaults to 1000
    :type delay_w: int, optional
    :param rate_w: rate window in hz in which the search is performed, defaults to 200
    :type rate_w: int, optional  
    """    

    snr_fring = AIPSTask('fring')
    snr_fring.inname = data.name
    snr_fring.inclass = data.klass
    snr_fring.indisk = data.disk
    snr_fring.inseq = data.seq
    snr_fring.refant = refant
    snr_fring.docalib = 1    # Apply CL tables
    snr_fring.gainuse = 0    # Apply the latest CL table
    snr_fring.solint = solint
    
    snr_fring.aparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    snr_fring.aparm[1] = 2    # At least 2 antennas per solution
    snr_fring.aparm[5] = 1    # Solve all IFs together
    snr_fring.aparm[6] = 2    # Amount of information printed
    snr_fring.aparm[7] = 5    # SNR cutoff   
    
    snr_fring.dparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    snr_fring.dparm[1] = 1    # Number of baseline combinations searched
    snr_fring.dparm[2] = delay_w   # Delay window (ns) 0 => Full Nyquist range
    snr_fring.dparm[3] = rate_w    # Rate window (mHz) 0 => Full Nyquist range
    snr_fring.dparm[5] = 1    # Stop at the FFT step
    #snr_fring.dparm[9] = 1    # Do NOT fit rates    
    
    snr_fring.snver = 3
    snr_fring.msgkill = -4
    
    snr_fring.go()
    
def snr_scan_list(data, full_source_list, log, version = 3):
    """Create a list of scans ordered by datapoints and SNR.

    Scans are first ordered by their SNR, then scans not using all antennas are dropped. \
    If there are no scans with all antennas available, only the ones with the maximum \
    number of antennas are taken into account. A warning will be printed if the best \
    scans has an SNR below 40.

    :param data: visibility data
    :type data: AIPSUVData
    :param full_source_list: list containing all sources in the dataset
    :type full_source_list: list of Source objects
    :param log: pipeline log
    :type log: file
    :param version: SN table version containing the SNR values, defaults to 3
    :type version: int, optional
    :return: ordered list of scans with SNR > 5, ordered list of scans where the maximum \
             number of antennas was observing
    :rtype: tuple of lists of Scan objects
    """    
    max_n_antennas = len(data.table('AN', 1))
    snr_table = data.table('SN', version)
    scan_list = []
    optimal_scan_list = []
    time_list = []
    for entry in snr_table:
        if entry['time'] not in time_list:
            a = SNRScan()
            a.time = entry['time']
            a.time_interval = entry['time_interval']
            scan_list.append(a)
            time_list.append(a.time)
            
        element = next(scan for scan in scan_list \
                       if scan.time == entry['time'])
        element.id = entry['source_id']
        element.antennas.append(entry['antenna_no'])
        try:
            element.snr.append(entry['weight_1'][0])
        except TypeError: # Single IF datasets
            element.snr.append(entry['weight_1'])
        
    # Order them by SNR
    scan_list.sort(key=lambda x: np.median(x.snr),\
                   reverse=True)
    # Drop no detections (SNR less than five)
    aux_list = []
    for s in scan_list:
        if np.median(s.snr) > 5:
            aux_list.append(s)
    scan_list = aux_list
    
    # If there are no scans, tell the main worflow to print an error message
    # and stop the pipeline
    
    if len(scan_list) == 0:
        return(404,404)
    
    for scans in scan_list:
        if len(scans.antennas) ==  max_n_antennas:
            optimal_scan_list.append(scans)
            
    # If there are no scans with all antennas, then the optimal
    # scan list is build with scans with the maximum number of
    # antennas
    if len(optimal_scan_list) == 0:
        max_n_antennas = 0
        for scans in scan_list:
            if len(scans.antennas) > max_n_antennas:
                max_n_antennas = len(scans.antennas)
        for scans in scan_list:
            if len(scans.antennas) ==  max_n_antennas:
                optimal_scan_list.append(scans)
    # Right now, the median includes the value at the reference 
    # antenna, which is always (SNR threshold + 1). This should be fixed.
    # Assign source names to both lists
    for scans in scan_list:
        for src in full_source_list:
            if scans.id == src.id:
                scans.name = src.name
    for scans in optimal_scan_list:
        for src in full_source_list:
            if scans.id == src.id:
                scans.name = src.name
    
    # Since both scan_list and optimal_scan_list are ordered by SNR, print
    # the ones that have been rejected due to few antennas
    
    if len(scan_list) != len(optimal_scan_list):
        print('\n')
        #log.write('\n')
        for s in scan_list:
            if s not in optimal_scan_list:
                print('A scan of ' + str(s.name) + ' with median SNR: '\
                      + '{:.2f} has been rejected '.format(np.median(s.snr)) \
                      + "since it's missing in " \
                      + str(max_n_antennas - len(s.antennas)) + ' antennas '\
                      + 'out of ' + str(max_n_antennas) + '.\n')
                    
                log.write('A scan of ' + s.name + ' with median SNR: '\
                      + '{:.2f} has been rejected '.format(np.median(s.snr)) \
                      + "since it's missing in " \
                      + str(max_n_antennas - len(s.antennas)) + ' antennas '\
                      + 'out of ' + str(max_n_antennas) + '.\n')
                    
    # Print a warning if the SNR of the calibrator is < 40
    if np.median(optimal_scan_list[0].snr) < 40:
        print('\nWARNING: The chosen scan has a low SNR. A better '\
              + 'calibrator might be found manually.\n')
        
        log.write('\nWARNING: The chosen scan has a low SNR. A better '\
              + 'calibrator might be found manually.\n')
            
    return(scan_list, optimal_scan_list)