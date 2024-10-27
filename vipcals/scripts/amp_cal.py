import numpy as np
import os

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

def amp_cal(data, antenna_list = [], solint = -3, average = 0, ref_if = 0):
    """Apply a-priori amplitude corrections
    
    This task takes as input a system temperature (TY) table and a 
    gain curve (GC) table and generates a solution (SN) table containing 
    amplitude gain calibration information.

    Creates SN#5 and CL#8.

    :param data: visibility data
    :type data: AIPSUVData
    :param antenna_list: antennas in which to perform amplitude calibration, \
                         defaults to []
    :type antenna_list: list of str
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
    apcal = AIPSTask('apcal')
    apcal.inname = data.name
    apcal.inclass = data.klass
    apcal.indisk = data.disk
    apcal.inseq = data.seq
    apcal.solint = solint

    apcal.antennas = AIPSList(antenna_list)
    #  apcal.sources = AIPSList(sources)
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
    clcal.snver = 5
    clcal.gainver = 7
    clcal.gainuse = 8
    clcal.msgkill = -4

    clcal.go()