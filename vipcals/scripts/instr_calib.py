from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

import numpy as np
import os

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

def pulse_phasecal(data, refant, cal_scan):
    """Correct instrumental phase delay using the PC table.
    
    Corrects instrumental phase delay of each source using their entries from the \
    pulse-calibration table (PC). A strong calibrator is used to eliminate any phase \
    ambiguity (see `VLBA Scientific Memo #8 <ME>`_). The solution is \
    applied to the calibration tables using CLCAL.
    
    .. _ME: https://library.nrao.edu/public/memos/vlba/sci/VLBAS_08.pdf

    Creates SN#4 and CL#7
    
    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param cal_scan: scan used for the calibration
    :type cal_scan: Scan object
    """        
    calib = cal_scan.name
    scan_time = cal_scan.time
    scan_time_interval = cal_scan.time_interval
    init_time = ddhhmmss(scan_time - 0.9*scan_time_interval/2)
    final_time = ddhhmmss(scan_time + 0.9*scan_time_interval/2)
    timer = [None] + init_time.tolist() + final_time.tolist()
    
    
    pccor = AIPSTask('pccor')
    pccor.inname = data.name
    pccor.inclass = data.klass
    pccor.indisk = data.disk
    pccor.inseq = data.seq
    pccor.refant = refant
    pccor.calsour = AIPSList([calib])
    pccor.timerang = timer
    pccor.snver = 4
    pccor.msgkill = -4
    
    pccor.go()

    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.opcode = 'calp'
    clcal.interpol = 'self'
    clcal.snver = 4
    clcal.gainver = 6
    clcal.gainuse = 7
    clcal.msgkill = -4
    
    clcal.go()

    
def manual_phasecal(data, refant, cal_scan):
    """Correct instrumental phase delay without using the PC table.
    
    Runs a fringe fit on a short scan of the calibrator .Then interpolates the solution \
    to the other sources using CLCAL.
    
    Creates SN#4 and CL#7

    :param data: _description_
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param cal_scan: scan used for the calibration
    :type cal_scan: Scan object
    """        
    calib = cal_scan.name
    scan_time = cal_scan.time
    scan_time_interval = cal_scan.time_interval
    init_time = ddhhmmss(scan_time - 0.9*scan_time_interval/2)
    final_time = ddhhmmss(scan_time + 0.9*scan_time_interval/2)
    timer = [None] + init_time.tolist() + final_time.tolist()
    
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
    
    phasecal_fring.aparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    phasecal_fring.aparm[1] = 2    # At least 2 antennas per solution
    phasecal_fring.aparm[5] = 0    # Solve IFs separatedly
    phasecal_fring.aparm[6] = 2    # Amount of information printed
    phasecal_fring.aparm[7] = 5    # SNR cutoff   
    
    phasecal_fring.dparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    phasecal_fring.dparm[1] = 1    # Number of baseline combinations searched
    phasecal_fring.dparm[2] = 500    # Delay window (ns)
    phasecal_fring.dparm[9] = 1    # Do NOT fit rates 
    
    phasecal_fring.snver = 4
    phasecal_fring.msgkill = -2
    
    # # Debugging line
    # print(phasecal_fring.inputs())
    
    phasecal_fring.go()
    
    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.opcode = 'calp'
    clcal.interpol = '2pt'
    clcal.snver = 4
    clcal.gainver = 6
    clcal.gainuse = 7
    clcal.msgkill = -4
    
    clcal.go()
    