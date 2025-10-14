import numpy as np

from AIPSTask import AIPSTask, AIPSList

AIPSTask.msgkill = -8

def amp_cal(data, solint = -3, average = False, ref_if = 0):
    """Apply a-priori amplitude corrections - APCAL
    
    Use the APCAL task in AIPS to generate an amplitude calibration table.    
    Takes as input the system temperature (TY) table and the 
    gain curve (GC) table and generates a solution (SN) table containing 
    amplitude gain calibration information.
    Creates SN#5 and CL#8.

    :param data: visibility data
    :type data: AIPSUVData
    :param solint: solution interval (min). If > 0, does not pay attention to 
        scan boundaries; defaults to -3
    :type solint: int, optional
    :param average: normalize Tsys by average Tsys; defaults to False
    :type average: bool, optional
    :param ref_if:
        if average = True and ref_if > 1:  ref_if is used as as the IF 
        to define the correct Tsys rather than the average over all IFs.
        if average = True and ref_if < 1: the mean value is used.
        if average = False, this parameter does nothing; defaults to 0
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

    if average == True:
        apcal.aparm[6] = 1
    else:
        apcal.aparm[6] = 0
    apcal.aparm[7] = ref_if

    apcal.go()
    
    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.opcode = 'CALP'
    clcal.interpol = 'SELF'
    clcal.snver = 5
    clcal.gainver = 7
    clcal.gainuse = 8

    clcal.go()