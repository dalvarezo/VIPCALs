from scripts.helper import ddhhmmss

from AIPSTask import AIPSTask, AIPSList
AIPSTask.msgkill = -8

def bp_correction(data, refant, calib_scans):
    """Apply complex bandpass correction to the data - BPASS

    Use the BPASS task in AIPS to create a BP table containing the 
    bandpass response function of the antennas.
    Creates BP#1

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param cal_scan: scans used for the calibration
    :type cal_scan: list of :class:`~vipcals.scripts.helper.Scan` objects
    """    
    calib_names = [x.source_name for x in calib_scans]
    # If there is only one scan, select its time interval
    if len(calib_scans) == 1:
        scan_time = calib_scans[0].time
        scan_time_interval = calib_scans[0].time_interval
        init_time = ddhhmmss(scan_time - 0.9*scan_time_interval/2)
        final_time = ddhhmmss(scan_time + 0.9*scan_time_interval/2)
        timer = [None] + init_time.tolist() + final_time.tolist()
    	
    bpass = AIPSTask('bpass')
    bpass.inname = data.name
    bpass.inclass = data.klass
    bpass.indisk = data.disk
    bpass.inseq = data.seq

    bpass.refant = refant    
    bpass.calsour = AIPSList(calib_names)
    if len(calib_scans) == 1:
        bpass.timerang = timer
    bpass.docalib = 1
    bpass.solint = -1  # Whole timerange

    bpass.weightit = 1  # Weight data by 1/sigma, more stable 

    bpass.bpassprm[5] = 0  # Divide by channel 0 
                           # (central 75 per cent of channels)
    bpass.bpassprm[9] = 1  # Interpolate over flagged channels
    bpass.bpassprm[10] = 6  # normalize amplitudes and zero average 
                            # phase using all channels in power, not
                            # voltage
    bpass.gainuse = 0
    bpass.outvers = 1
    
    bpass.go()