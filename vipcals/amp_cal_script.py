from AIPS import AIPS
from AIPSData import AIPSUVData
from AIPSTask import AIPSTask, AIPSList

import numpy as np


#################
#               #
#    CLASSES    #
#               #
#################


class Scan():
    """Scans within an observation.""" 
    def __init__(self):
        self.name = None
        self.id = None
        self.snr = []
        self.time = None
        self.itime = None
        self.ftime = None
        self.time_interval = None
        self.antennas = []
        self.calib_antennas = []


#################
#               #
#   FUNCTIONS   #
#               #
#################

def amp_cal(data, solint = -3, average = 0, ref_if = 0):
    """Apply a-priori amplitude corrections
    
    This task takes as input a system temperature (TY) table and a 
    gain curve (GC) table and generates a solution (SN) table containing 
    amplitude gain calibration information.

    :param data: visibility data
    :type data: AIPSUVData
    :param solint: solution interval (min). If > 0, does not pay attention to 
        scan boundaries, defaults to -3
    :type solint: int, optional
    :param average: if > 0 => normalize Tsys by average Tsys, defaults to 0
    :type average: int, optional
    :param ref_if: if average > 0, ref_if is used as as the IF to define the
        correct Tsys rather than the average over all IFs.
        if average > 0 and ref_if < 1, the mean value is used.
        if average = 0, this parameter does nothing , defaults to 0
    :type ref_if: int, optional
    """    
    # Check which antennas have GC, only calibrate those
    gc_antennas = [y['antenna_no'] for y in data.table('GC',1)]
    antenna_list = list(set(gc_antennas))

    apcal = AIPSTask('apcal')
    apcal.inname = data.name
    apcal.inclass = data.klass
    apcal.indisk = data.disk
    apcal.inseq = data.seq
    apcal.solint = solint

    apcal.antennas = AIPSList(antenna_list)
    apcal.aparm[6] = average
    apcal.aparm[7] = ref_if
    apcal.msgkill = -4

    apcal.go()

    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.opcode = 'calp'
    clcal.interpol = 'self'
    clcal.snver = data.table_highver('SN')
    clcal.gainver = 0
    clcal.gainuse = 0
    clcal.msgkill = -4

    clcal.go()

def bp_correction(data, refant, calib_scans):
    """Apply complex bandpass correction to the data.

    Generates BP#1

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param cal_scan: scans used for the calibration
    :type cal_scan: list of Scan object
    """    
    calib_names = [x.name for x in calib_scans]

    # If there is only one scan, give the time as an input
    if len(calib_scans) == 1:
        if calib_scans[0].itime == None:
            scan_time = calib_scans[0].time
            scan_time_interval = calib_scans[0].time_interval
            init_time = ddhhmmss(scan_time - 0.9*scan_time_interval/2)
            final_time = ddhhmmss(scan_time + 0.9*scan_time_interval/2)
            timer = [None] + init_time.tolist() + final_time.tolist()
        else:
            timer = [None] + calib_scans[0].itime + calib_scans[0].ftime

        
    	
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
    
    bpass.bpassprm[1:] = [0,0,0,0,0,0,0,0,0,0,0]  # Reset parameters
    bpass.bpassprm[5] = 0  # Divide by channel 0 (central 75 per cent of channels)
    bpass.bpassprm[9] = 1  # Interpolate over flagged channels
    bpass.bpassprm[10] = 6  # normalize amplitudes and zero average 
                            # phase using all channels in power, not
                            # voltage
    bpass.gainuse = 0
    bpass.outvers = 1
    bpass.msgkill = -4
    
    bpass.go()

def correct_autocorr(data, solint = -5):
    """Correct errors in the scaling of auto correlations due to the bandpass.

    ACSCL

    :param data: visibility data
    :type data: AIPSUVData
    :param solint: solution interval in minutes. \
    If > 0, does not pay attention to scan boundaries. \
    Defaults to -5
    :type solint: float, optional
    """    
    acscl = AIPSTask('acscl')
    acscl.inname = data.name
    acscl.inclass = data.klass
    acscl.indisk = data.disk
    acscl.inseq = data.seq
    acscl.solint = solint 

    acscl.docalib = 1
    acscl.gainuse = 0
    acscl.doband = 1
    acscl.msgkill = -2  

    acscl.go()

    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.opcode = 'calp'
    clcal.interpol = 'self'
    clcal.snver = data.table_highver('SN')
    clcal.gainver = 0
    clcal.gainuse = 0
    clcal.msgkill = -4

    clcal.go()

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

def get_calib_scans(data, ordered_scan_list, refant):
    """Get the scans that will be used for calibration steps.

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param ordered_scan_list: scan list ordered by SNR
    :type ordered_scan_list: lists of SNRScan objects
    """    
    # Retrieve all antennas with TY and GC
    all_antennas = [x['nosta'] for x in data.table('AN', 1)]
    gc_antennas = list(set([y['antenna_no'] for y in data.table('GC',1)]))
    ty_antennas = list(set([z['antenna_no'] for z in data.table('TY', 2)]))

    available_antennas = [z for z in all_antennas if z in ty_antennas and\
                          z in gc_antennas]
    covered_antennas = []
    # Look only at scans where the reference antenna is available
    scan_list = [s for s in ordered_scan_list if refant in s.antennas]

    # Fill the calib_scan_list until all antennas are covered
    calib_scan_list = []
    for s in scan_list:
        s.calib_antennas = [x for x in s.antennas if x not in covered_antennas] \
                            + [refant]
        
        if len(s.calib_antennas) > 1:
            calib_scan_list.append(s)
            covered_antennas += s.calib_antennas
            covered_antennas = list(set(covered_antennas))

        if set(covered_antennas) == set(available_antennas):
            break

    return(calib_scan_list)

def manual_phasecal_multi(data, refant, calib_scans):
    """Correct instrumental phase delay with multiple calibrators without the PC table.
    
    Runs a fringe fit on a short scan of the calibrators, creating multiple SN tables.
    Then, merges the solutions and interpolates them to the other sources using 
    CLCAL.
    
    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param calib_scans: list of scans used for the calibration
    :type calib_scans: list of Scan object
    """        

    sn_version = data.table_highver('SN') + 1 # First SN table to create

    for n, scan in enumerate(calib_scans):
        calib = scan.name
        if scan.itime == None:
            scan_time = scan.time
            scan_time_interval = scan.time_interval
            init_time = ddhhmmss(scan_time - 0.9*scan_time_interval/2)
            final_time = ddhhmmss(scan_time + 0.9*scan_time_interval/2)
            timer = [None] + init_time.tolist() + final_time.tolist()
        else:
            timer = [None] + calib_scans[0].itime + calib_scans[0].ftime
        
        phasecal_fring = AIPSTask('fring')
        phasecal_fring.inname = data.name
        phasecal_fring.inclass = data.klass
        phasecal_fring.indisk = data.disk
        phasecal_fring.inseq = data.seq
        phasecal_fring.refant = refant
        phasecal_fring.docalib = 1    # Apply CL tables
        phasecal_fring.gainuse = 0    # Apply the latest CL table    
        
        phasecal_fring.calsour = AIPSList([calib])
        phasecal_fring.timerang = timer
        
        phasecal_fring.antennas = AIPSList(scan.calib_antennas)

        phasecal_fring.aparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
        phasecal_fring.aparm[1] = 2    # At least 2 antennas per solution
        phasecal_fring.aparm[5] = 0    # Solve IFs separatedly
        phasecal_fring.aparm[6] = 2    # Amount of information printed
        phasecal_fring.aparm[7] = 5    # SNR cutoff   
        
        phasecal_fring.dparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
        phasecal_fring.dparm[1] = 1    # Number of baseline combinations searched
        phasecal_fring.dparm[2] = 1000    # Delay window (ns)
        phasecal_fring.dparm[9] = 1    # Do NOT fit rates 
        
        phasecal_fring.snver = sn_version + n
        phasecal_fring.msgkill = -2
        
        phasecal_fring.go()
    
    # If multiple calib scans, merge tables producing SN(4+n+1)
    
    if n > 0:
        clcal_merge = AIPSTask('clcal')
        clcal_merge.inname = data.name
        clcal_merge.inclass = data.klass
        clcal_merge.indisk = data.disk
        clcal_merge.inseq = data.seq

        clcal_merge.opcode = 'MERG'
        clcal_merge.snver = sn_version # First table to merge
        clcal_merge.invers = sn_version + n # Last table to merge
        clcal_merge.refant = refant

        clcal_merge.go()

    # Apply solutions

    clcal_apply = AIPSTask('clcal')
    clcal_apply.inname = data.name
    clcal_apply.inclass = data.klass
    clcal_apply.indisk = data.disk
    clcal_apply.inseq = data.seq
    clcal_apply.opcode = 'calp'
    clcal_apply.interpol = '2pt'
    clcal_apply.snver = sn_version + n + 1
    clcal_apply.gainver = 0
    clcal_apply.gainuse = 0
    clcal_apply.msgkill = -4
    
    clcal_apply.go()
    
    # If multiple calib scans, 
    # remove previous tables and leave only the merged one
    if n > 0:
        for i in range (sn_version, sn_version+n+1):
            data.zap_table('SN', i)
        tacop(data, 'SN', sn_version+n+1, sn_version)
        data.zap_table('SN', sn_version+n+1)    


def sampling_correct(data, solint = -3):
    """Digital sampling correction
    
    Correct cross correlations using auto correlations.

    :param data: visibility data
    :type data: AIPSUVData
    :param solint: solution interval in minutes. \
    If > 0, does not pay attention to scan boundaries. \
    Defaults to -3
    :type solint: float, optional
    """    
    accor = AIPSTask('accor')
    accor.inname = data.name
    accor.inclass = data.klass
    accor.indisk = data.disk
    accor.inseq = data.seq
    accor.solint = solint 
    accor.msgkill = -2  

    accor.go()

    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.opcode = 'calp'
    clcal.interpol = 'self'
    clcal.snver = data.table_highver('SN')
    clcal.gainver = 0 
    clcal.gainuse = 0 
    clcal.msgkill = -4

    clcal.go()

def snr_fring_only_fft(data, refant, solint = 0, delay_w = 1000, \
                       rate_w = 200):
    """Short fringe fit (only FFT) to select bright calibrators.
    
    Fringe fit of all IF's together, solving for delays and rates. Default values for \
    the delay and rate windows are 1000 ns and 200hz.

    Creates SN#1, which contains the SNR per scan. 

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

    snr_fring.msgkill = -4

    snr_fring.go()

def snr_scan_list_v2(data, version = 1):
    """Create a list of scans ordered by SNR.

    Scans are returned ordered by their SNR. A warning will be printed \
    if the best scan has an SNR below 40.

    :param data: visibility data
    :type data: AIPSUVData
    :param version: SN table version containing the SNR values, defaults to 1
    :type version: int, optional
    :return: ordered list of scans with SNR > 5
    :rtype: list of SNRScan objects
    """    
    snr_table = data.table('SN', version)
    scan_list = []
    time_list = []
    for entry in snr_table:
        if entry['time'] not in time_list:
            a = Scan()
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
    
    # If there are no scans, tell the main worflow to print an error message
    # and stop the pipeline
    if len(scan_list) == 0:
        return(404)
    
    # Right now, the median includes the value at the reference 
    # antenna, which is always (SNR threshold + 1). This should be fixed.
    
    # Assign source names to the lists
    for scans in scan_list:
        for src in data.table('SU', 1):
            if scans.id == src.id__no:
                scans.name = src.source.strip()
    return(scan_list)

def tacop(data, ext, invers, outvers):
    """Copy one calibration table to another.

    Copies one AIPS calibration table from one version to another one.

    :param data: visibility data
    :type data: AIPSUVData
    :param ext: table extension
    :type ext: str
    :param invers: input version
    :type invers: int
    :param outvers: output version
    :type outvers: int
    """
    tacop = AIPSTask('tacop')
    tacop.inname = data.name
    tacop.inclass = data.klass
    tacop.indisk = data.disk
    tacop.inseq = data.seq

    tacop.outname = data.name
    tacop.outclass = data.klass
    tacop.outdisk = data.disk
    tacop.outseq = data.seq

    tacop.inext = ext
    tacop.invers = invers
    tacop.outvers = outvers
    tacop.msgkill = -4

    tacop.go()

def ty_smooth(data, tmin = 0, tmax = 1000, time_interv = 15, max_dev = 250):
    """Smooth/filter system temperature tables.
    
    Flag TSys values below tmin and above tmax. Also values that
    deviate more than (max_dev) K from a mean value. This is done on a 
    per-source basis. 

    Flag also antennas with no TY or GC table entries.
    
    Creates TY#2 and FG#2

    :param data: visibility data
    :type data: AIPSUVData
    :param tmin: minimum TSys value allowed in K, defaults to 0
    :type tmin: float, optional
    :param tmax: maximum TSys value allowed in K, defaults to 1000
    :type tmax: float, optional
    :param time_interv:  smoothing time interval in minutes, defaults to 15
    :type time_interv: float, optional
    :param max_dev: maximum TSys deviation allowed from the mean value of each \
        source in K; defaults to 250
    :type max_dev: float, optional

    :return: list of ids of antennas with no system temperature information
    :rtype: list of int
    :return: list of ids of antennas with no gain curve information
    :rtype: list of int
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

    # Flag antennas with no Tsys or GC information

    all_antennas = []
    for a in data.table('AN',1):
        all_antennas.append(a['nosta'])

    antennas_w_tsys = []
    for t in data.table('TY', 2):
        antennas_w_tsys.append(t['antenna_no'])
    antennas_w_tsys = list(set(antennas_w_tsys))

    antennas_w_gc = [y['antenna_no'] for y in data.table('GC',1)]

    bad_antennas = [z for z in all_antennas if z not in antennas_w_tsys or \
                    z not in antennas_w_gc]

    antennas_no_tsys = [a for a in all_antennas if a not in antennas_w_tsys]
    antennas_no_gc = [b for b in all_antennas if b not in antennas_w_gc]

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
        uvflg.reason = 'NO TSYS'
        uvflg.msgkill = -4

        uvflg.go()

    return(antennas_no_tsys, antennas_no_gc)

##############################################################################
##############################################################################

if __name__ == "__main__":

    #################
    #               #
    #    INPUTS     #
    #               #
    #################

    AIPS.userno = 4

    # Name, class, seq and disk of the entry in AIPS
    aips_name = 'TEST'
    klass = 'UVDATA'
    disk_number = 1
    seq = 1

    # Reference antenna number or name
    refant = 5

    # Look for calibrator scans?
    look_calib_scans = True

    # If not, give calibrator scan manually
    if look_calib_scans == False:
        calib_name = 'J0555+3948'
        # Scan initial/final time in format [DAY,HOUR,MINUTE,SECOND]
        initial_time = [0,16,22,11]
        final_time = [0,16,26,2]

    # Correct instrumental delays?
    corr_inst_del = True

    ##############################################################################
    ##############################################################################

    #################
    #               #
    #   WORKFLOW    #
    #               #
    #################

    uvdata = AIPSUVData(aips_name, klass, disk_number, seq)

    # If reference antenna is given as a name, get antenna number
    if type(refant) == str:
        for a in uvdata.table('AN', 0):
            if refant in a.anname:
                refant = a.nosta
                break

    if type(refant) == str:
        print("{refant} not found in the AN table")
        exit(1)

    # Tsys flagging
    no_tsys_ant, no_gc_ant = ty_smooth(uvdata)

    if look_calib_scans is True:
        # Fringe fit to get the SNR
        snr_fring_only_fft(uvdata, refant)
        # List of scans ordered by SNR
        scan_list = snr_scan_list_v2(uvdata)
        # Get the calibrator scans
        calibrator_scans = get_calib_scans(uvdata, scan_list, refant)
    else:
        calibrator_scans = [Scan()]
        calibrator_scans[0].name = calib_name
        calibrator_scans[0].itime = initial_time
        calibrator_scans[0].ftime = final_time
        calibrator_scans[0].antennas = [x['nosta'] for x in uvdata.table('AN', 1)]
        calibrator_scans[0].calib_antennas = [x['nosta'] for x in uvdata.table('AN', 1)]

    # Sampling correction - ACCOR
    sampling_correct(uvdata)

    # Correct for instrumental delays
    if corr_inst_del is True:
        manual_phasecal_multi(uvdata, refant, calibrator_scans)

    # Bandpass
    bp_correction(uvdata, refant, calibrator_scans)

    # Autocorrelations scaling - ACSCL
    correct_autocorr(uvdata)

    # Amplitude calibration - APCAL
    amp_cal(uvdata)

    print("Scans used as calibrators:\n")
    for s in calibrator_scans:
        if s.itime == None:
            print(f"{s.name} \n\t SNR: {round(np.median(s.snr),2)} \
                \n\t Start time: {ddhhmmss(s.time - s.time_interval/2)}\
                \n\t Antennas: {list(set(s.calib_antennas))}\n")
        else:
            print(f"{s.name}\
                \n\t Start time: {(s.itime)}\
                \n\t Antennas: {list(set(s.calib_antennas))}\n")