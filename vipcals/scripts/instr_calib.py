from scripts.helper import ddhhmmss, tacop

from AIPSTask import AIPSTask, AIPSList
AIPSTask.msgkill = -8

def pulse_phasecal(data, refant, cal_scan):
    """Correct instrumental phase delay using the PC table.
    
    Corrects instrumental phase delay of each source using their entries from the 
    pulse-calibration table (PC) using the PCCOR task in AIPS. A strong calibrator is 
    used to eliminate any phase ambiguity (see `VLBA Scientific Memo #8 <ME>`_). The 
    solution is applied to the calibration tables using the CLCAL task in AIPS.

    Creates SN#3 and CL#6

    THIS FUNCTION IS NOT USED IN THE CURRENT VERSION OF THE PIPELINE.
    
    .. _ME: https://library.nrao.edu/public/memos/vlba/sci/VLBAS_08.pdf
    
    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param cal_scan: scan used for the calibration
    :type cal_scan: :class:`~vipcals.scripts.helper.Scan` object
    """        
    calib = cal_scan.source_name
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
    pccor.snver = 3
    
    pccor.go()

    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.opcode = 'calp'
    clcal.interpol = 'self'
    clcal.snver = 3
    clcal.gainver = 5
    clcal.gainuse = 6
    
    clcal.go()

    
def manual_phasecal_multi(data, refant, calib_scans):
    """Correct instrumental phase delay using multiple bright calibrators.
    
    Uses the FRING task to runs a fringe fit on a short scan of the calibrators, 
    creating multiple SN tables. Then, merges the solutions in SN#4 and interpolates 
    them to the other sources using the CLCAL task in AIPS.
    
    Creates SN#3 and CL#6

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param calib_scans: list of scans used for the calibration
    :type calib_scans: list of :class:`~vipcals.scripts.helper.FFtarget` object
    """        

    for n, scan in enumerate(calib_scans):
        calib = scan.source_name
        scan_time = scan.time
        scan_time_interval = scan.time_interval
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
        
        phasecal_fring.antennas = AIPSList(scan.calib_antennas)

        phasecal_fring.aparm[1] = 2    # At least 2 antennas per solution
        phasecal_fring.aparm[5] = 0    # Solve IFs separatedly
        phasecal_fring.aparm[6] = 2    # Amount of information printed
        phasecal_fring.aparm[7] = 5    # SNR cutoff   
        
        phasecal_fring.dparm[1] = 1    # Number of baseline combinations searched
        phasecal_fring.dparm[2] = 1000    # Delay window (ns)
        phasecal_fring.dparm[8] = 1    # Zero rates after the fit 
        
        phasecal_fring.snver = 3 + n
        
        phasecal_fring.go()
    
    # If multiple calib scans, merge tables producing SN(3+n+1)
    
    if n > 0:
        clcal_merge = AIPSTask('clcal')
        clcal_merge.inname = data.name
        clcal_merge.inclass = data.klass
        clcal_merge.indisk = data.disk
        clcal_merge.inseq = data.seq

        clcal_merge.opcode = 'MERG'
        clcal_merge.snver = 3 # First table to merge
        clcal_merge.invers = 3+n # Last table to merge
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
    clcal_apply.snver = 3 + n + 1
    clcal_apply.gainver = 5
    clcal_apply.gainuse = 6
    
    clcal_apply.go()
    
    # If multiple calib scans, 
    # remove previous tables and leave only the merged one
    if n > 0:
        for i in range (3, 3+n+1):
            data.zap_table('SN', i)
        tacop(data, 'SN', 3+n+1, 3)
        data.zap_table('SN', 3+n+1)    