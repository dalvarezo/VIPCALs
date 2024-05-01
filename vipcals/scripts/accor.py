import numpy as np
import os

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

def sampling_correct(data, solint = -3):
    """Digital sampling correction
    
    Correct cross correlations using auto correlations.
    
    Creates SN#1 and CL#4.

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
    clcal.snver = 1
    clcal.gainver = 3
    clcal.gainuse = 4
    clcal.msgkill = -4

    clcal.go()