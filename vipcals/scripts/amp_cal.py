import numpy as np
import os

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

def amp_cal(data, sources, solint = -3, average = 0, ref_if = 0):
    """Apply a-priori amplitude corrections
    
    This task takes as input a system temperature (TY) table and a 
    gain curve GC table and generates a solution (SN) table containing 
    amplitude gain calibration information.

    Creates SN#2 and CL#5.

    :param data: visibility data
    :type data: AIPSUVData
    :param sources: list of Source() objects
    :type sources: _type_
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
    apcal.sources = AIPSList(sources)
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
    clcal.snver = 2
    clcal.gainver = 4
    clcal.gainuse = 5
    clcal.msgkill = -4

    clcal.go()