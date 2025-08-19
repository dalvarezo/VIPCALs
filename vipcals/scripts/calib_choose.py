import numpy as np

from AIPSTask import AIPSTask, AIPSList

AIPSTask.msgkill = -8

from scripts.helper import NoScansError
from scripts.helper import Scan
from scripts.helper import tacop
    
def snr_fring(data, refant, priority_refants, delay_w = 1000, rate_w = 200):
    """Short fringe fit (only FFT) to select a bright calibrator.
    
    Fringe fit of all sources using FRING task in AIPS. It solves for delays 
    and rates of each IFs and stopping at the FFT stage (no least square solution). 
    The solution interval is automatically set so that it only creates one solution 
    per scan. It creates a solution table (SN) which contains the signal-to-noise 
    ratio (SNR) of each scan. Default values for the delay and rate windows 
    are 1000 ns and 200hz.

    Creates SN#1, which contains the SNR per scan. 

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param priority_refants: list of alternatives to the reference antenna
    :param priority_refants: list of int
    :param delay_w: delay window in ns in which the search is performed; 
        defaults to 1000
    :type delay_w: int, optional
    :param rate_w: rate window in mHz in which the search is performed; 
        defaults to 200
    :type rate_w: int, optional  
    """    
    nx_table = data.table('NX', 1)
    longest_scan = np.ceil(max([x.time_interval for x in nx_table]) * 24 * 60)

    snr_fring = AIPSTask('fring')
    snr_fring.inname = data.name
    snr_fring.inclass = data.klass
    snr_fring.indisk = data.disk
    snr_fring.inseq = data.seq
    snr_fring.refant = refant
    snr_fring.docalib = 1    # Apply CL tables
    snr_fring.gainuse = 0    # Apply the latest CL table
    snr_fring.solint = int(longest_scan)
    
    snr_fring.aparm[1] = 2    # At least 2 antennas per solution
    snr_fring.aparm[5] = 0    # Solve each IF separately
    snr_fring.aparm[6] = 2    # Amount of information printed
    snr_fring.aparm[7] = 5    # SNR cutoff   
    snr_fring.aparm[9] = 1    # Exhaustive search
    snr_fring.search = AIPSList(priority_refants[:10])
    
    snr_fring.dparm[1] = 1    # Number of baseline combinations searched
    snr_fring.dparm[2] = delay_w   # Delay window (ns) 0 => Full Nyquist range
    snr_fring.dparm[3] = rate_w    # Rate window (mHz) 0 => Full Nyquist range
    snr_fring.dparm[5] = 1    # Stop at the FFT step 
    
    snr_fring.snver = 1
    
    snr_fring.go()
    

def snr_scan_list_v2(data, version = 1):
    """Create a list of scans ordered by SNR.

    The solution table (SN) produced by snr_fring is read and returns a list 
    of :class:`~vipcals.scripts.helper.Scan` objects ordered by their median SNR 
    over all antennas. 

    :param data: visibility data
    :type data: AIPSUVData
    :param version: SN table version containing the SNR values; defaults to 1
    :type version: int, optional
    :return: list of scans ordered by median SNR
    :rtype: list of :class:`~vipcals.scripts.helper.Scan` objects
    """    
    snr_table = data.table('SN', version)
    scan_list = []
    time_list = []
    for entry in snr_table:
        # Create a new Scan() for each new timestamp
        if entry['time'] not in time_list:
            a = Scan()
            a.time = entry['time']
            a.time_interval = entry['time_interval']
            scan_list.append(a)
            time_list.append(a.time)
            
        element = next(scan for scan in scan_list \
                       if scan.time == entry['time'])
        element.source_id = entry['source_id']
        element.antennas.append(entry['antenna_no'])

        # Append the SNR value of each antenna (except the reference antenna)
        if type(entry['weight_1']) == list:
            if entry.antenna_no != entry.refant_1[0]:
                element.snr.append([x/2 for x in entry['weight_1']])
            else:
                element.snr.append([np.nan])
        else: # Single IF datasets
            if entry.antenna_no != entry.refant_1:
                element.snr.append(entry['weight_1']/2)
            else:
                element.snr.append(np.nan)

    # Order them by their median SNR
    if type(entry['weight_1']) == list:
        scan_list.sort(key=lambda x: np.nanmedian([a for b in x.snr for a in b]),\
                    reverse=True)
    else: # Single IF datasets
        scan_list.sort(key=lambda x: np.nanmedian(x.snr),\
                    reverse=True)
    
    # If there are no scans, tell the main worflow to print an error message
    # and stop the pipeline
    if len(scan_list) == 0:
        raise NoScansError
    
    # Assign source names to the Scan objects
    for scans in scan_list:
        for src in data.table('SU', 1):
            if scans.source_id == src.id__no:
                scans.source_name = src.source.strip()

    return(scan_list)

def get_calib_scans(data, ordered_scan_list, refant):
    """Get the scans that will be used for calibration steps.

    For each antenna, search in the scan list generated by :function:`~vipcals.scripts.calib_choose.snr_scan_list_v2` 
    for the scan with the highest SNR. If there are any antennas where the highest SNR is 
    lower than 5, they are flagged in FG#3 by :function:`~vipcals.scripts.calib_choose.flag_antennas_v2`.

    Returns a list of calibrator :class:`~vipcals.scripts.helper.Scan` with the antennas 
    covered by each of them, as well as the flagged antennas if any. 

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param ordered_scan_list: scan list ordered by SNR
    :type ordered_scan_list: lists of :class:`~vipcals.scripts.helper.Scan` objects
    :return: list of scans ordered by median SNR, list of flagged antennas
    :rtype: list of :class:`~vipcals.scripts.helper.Scan` objects, list of int
    """    
    # Drop scans not available for the reference antenna or with 0 seconds of observing time
    scan_list = []
    for s in ordered_scan_list:
        if refant in s.antennas and s.time_interval > 0.0:
            scan_list.append(s)

    best_scans = {}

    for s in scan_list:
        try: 
            _ = len(s.snr[0])>1
            for ant, snr in zip(s.antennas, [sum(inner) / len(inner) for inner in s.snr]):  
                if ant == refant:
                    continue     
                if ant not in best_scans or snr > best_scans[ant][1]:
                    best_scans[ant] = (s, snr)
        except TypeError: # Single IF
            for ant, snr in zip(s.antennas, s.snr):  
                if ant == refant:
                    continue     
                if ant not in best_scans or snr > best_scans[ant][1]:
                    best_scans[ant] = (s, snr)

    # Remove antennas that did not reach 5 of SNR
    no_calib_antennas = [ant for ant in best_scans if best_scans[ant][1] < 5 
                         or np.isnan(best_scans[ant][1])]
    for nca in no_calib_antennas:
        del best_scans[nca]

    flag_antennas_v2(data, no_calib_antennas)

    calib_scan_list = []

    for s in ordered_scan_list:
        s.calib_antennas = [ant for ant in best_scans if best_scans[ant][0] == s]
        s.calib_snr = [round(best_scans[ant][1],2) for ant in best_scans if best_scans[ant][0] == s]
        if len(s.calib_antennas) != 0:
            s.calib_antennas += [refant]
            calib_scan_list.append(s)


    return(calib_scan_list, no_calib_antennas)

def flag_antennas_v2(data, antennas):
    """Flag antennas due to missing calibrator scans.

    Produces FG#3

    :param data: visibility data
    :type data: AIPSUVData
    :param antennas: antenna codes to be flagged
    :type antennas: list of int
    """    

    # Copy FG2 to FG3
    tacop(data, 'FG', 2, 3)
    
    if len(antennas) > 0:

        # Apply antennas flags 
        uvflg = AIPSTask('uvflg')
        uvflg.inname = data.name
        uvflg.inclass = data.klass
        uvflg.indisk = data.disk
        uvflg.inseq = data.seq

        uvflg.antennas = AIPSList(antennas)
        uvflg.outfgver = 3
        uvflg.reason = 'NO CALIBRATOR'

        uvflg.go()